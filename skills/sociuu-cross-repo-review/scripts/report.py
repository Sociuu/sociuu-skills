#!/usr/bin/env python3
"""Validate and render source-backed advisory review reports.

Structural validation checks receipts and presence of evidence. It cannot establish
whether an agent's semantic finding or evidence statement is true.
"""
import argparse
import html
import json
from pathlib import Path
import re


SHA = re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})\Z')
NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]*\Z')
QUICK_ACTION = re.compile(r'(?m)^(\s*)/([A-Za-z][A-Za-z0-9_-]*)')
MARKDOWN = re.compile(r'([\\`*_{}\[\]()#+!>|~])')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def obj(value, fields, label):
    require(isinstance(value, dict) and all(key in value for key in fields), f'{label} requires {", ".join(fields)}')
    return value


def string(value, label):
    require(isinstance(value, str) and bool(value.strip()), f'{label} must be nonempty text')
    return value


def strings(value, label, nonempty=False):
    require(isinstance(value, list) and (not nonempty or bool(value)), f'{label} must be a list')
    for item in value:
        string(item, label + ' item')
    return value


def choice(value, allowed, label):
    require(value in allowed, f'invalid {label}')


def sha(value, label):
    require(isinstance(value, str) and bool(SHA.fullmatch(value)), f'{label} must be a full Git SHA')


def path(value, label):
    string(value, label)
    require(not value.startswith('/') and not value.startswith('\\') and not re.match(r'^[A-Za-z]:', value)
            and '\\' not in value and all(part not in ('', '.', '..') for part in value.split('/')), f'{label} must be repository-relative without traversal')


def receipt_scope(receipt, scope, label):
    obj(receipt, ('scope', 'status'), label)
    actual = obj(receipt['scope'], ('base', 'head_sha'), label + ' scope')
    require(all(actual[key] == scope[key] for key in ('base', 'head_sha')), f'{label} source scope differs')
    require(receipt['status'] == 'complete', f'{label} is not complete')


def manifest_scope(report, manifest_lock):
    obj(manifest_lock, ('version', 'composite', 'repositories'), 'snapshot receipt')
    require(type(manifest_lock['version']) is int and manifest_lock['version'] == 1,
            'unsupported snapshot receipt version')
    composite = obj(manifest_lock['composite'], ('base', 'head'), 'snapshot composite')
    require(composite['base'] == report['source_scope']['base'] and
            composite['head'] == report['source_scope']['head_sha'], 'snapshot composite scope differs')
    require(isinstance(manifest_lock['repositories'], list), 'snapshot repositories must be a list')
    expected = {}
    for repo in manifest_lock['repositories']:
        obj(repo, ('name', 'base', 'head', 'role'), 'snapshot repository')
        require(isinstance(repo['name'], str) and repo['name'] not in expected,
                'invalid or duplicate snapshot repository')
        expected[repo['name']] = {key: repo[key] for key in ('base', 'head', 'role')}
    actual = {repo['name']: {key: repo[key] for key in ('base', 'head', 'role')}
              for repo in report['repositories']}
    require(actual == expected, 'report repositories differ from the reviewed snapshot')


def finding_dispositions(report, ce_receipt, integration_receipt):
    raw = {}
    for stage, receipt, id_key in (('ce', ce_receipt, '#'), ('integration', integration_receipt, 'id')):
        if receipt is None:
            continue
        obj(receipt, ('status',), stage + ' receipt')
        choice(receipt['status'], ('complete', 'degraded', 'failed', 'skipped'), stage + ' receipt status')
        findings = receipt.get('findings', [] if receipt['status'] != 'complete' else None)
        require(isinstance(findings, list), stage + ' receipt requires findings')
        if 'scope' not in receipt:
            require(receipt['status'] != 'complete' and not findings,
                    'unscoped receipt cannot establish findings or completion')
            continue
        scope = obj(receipt['scope'], ('base', 'head_sha'), stage + ' scope')
        require(all(scope[key] == report['source_scope'][key] for key in ('base', 'head_sha')),
                stage + ' receipt scope differs')
        for finding in findings:
            obj(finding, (id_key, 'severity'), stage + ' finding')
            choice(finding['severity'], ('P0', 'P1', 'P2', 'P3'), stage + ' finding severity')
            identifier = finding[id_key]
            require(type(identifier) in (str, int) and str(identifier).strip(), 'invalid source finding ID')
            key = (stage, str(identifier))
            require(key not in raw, 'duplicate source finding ID')
            raw[key] = finding
    require(isinstance(report['finding_dispositions'], list), 'finding dispositions must be a list')
    accounted = set()
    reported = {finding['id']: finding for finding in report['findings']}
    retained = {identifier: set() for identifier in reported}
    for item in report['finding_dispositions']:
        obj(item, ('stage', 'source_id', 'action', 'reason', 'evidence'), 'finding disposition')
        choice(item['stage'], ('ce', 'integration'), 'disposition stage')
        string(item['source_id'], 'disposition source ID')
        key = (item['stage'], item['source_id'])
        require(key in raw and key not in accounted, 'unknown or duplicate finding disposition')
        accounted.add(key)
        choice(item['action'], ('retained', 'rejected', 'reclassified'), 'disposition action')
        string(item['reason'], 'disposition reason')
        strings(item['evidence'], 'disposition evidence', item['action'] != 'retained')
        if item['action'] in ('retained', 'reclassified'):
            identifier = item.get('finding_id')
            require(isinstance(identifier, str) and identifier in retained, 'disposition finding is not reported')
            retained[identifier].add(item['stage'])
            source, destination = raw[key], reported[identifier]
            source_materiality = source.get('materiality', 'consequential' if source['severity'] != 'P3' else None)
            changed = (source['severity'] != destination['severity'] or
                       source.get('validation_status', 'confirmed') != destination['validation_status'] or
                       source_materiality is not None and source_materiality != destination['materiality'])
            require(not changed or item['action'] == 'reclassified',
                    'changed finding severity, validation or materiality requires explicit reclassification evidence')
        else:
            require('finding_id' not in item, 'rejected disposition cannot retain a finding')
    require(accounted == set(raw), 'receipt findings are missing from the disposition accounting')
    if report['status'] == 'complete':
        for finding in report['findings']:
            needed = {'CE': {'ce'}, 'integration': {'integration'},
                      'both': {'ce', 'integration'}, 'analyzer': set()}[finding['origin']]
            require(needed <= retained[finding['id']], 'reported finding lacks its declared review provenance')


def validate_report(report, ce_receipt=None, integration_receipt=None, manifest_lock=None):
    obj(report, ('version', 'status', 'source_scope', 'repositories', 'intent', 'summary',
                 'walkthrough', 'findings', 'checks', 'qa_runbook', 'diagrams', 'diagram_notes',
                 'coverage_limits', 'integration_status', 'finding_dispositions'), 'report')
    require(type(report['version']) is int and report['version'] == 1, 'unsupported report version')
    choice(report['status'], ('complete', 'degraded', 'failed'), 'report status')
    scope = obj(report['source_scope'], ('base', 'head_sha'), 'source scope')
    sha(scope['base'], 'source base')
    sha(scope['head_sha'], 'source head')
    string(report['intent'], 'intent')
    repositories = report['repositories']
    require(isinstance(repositories, list) and repositories, 'repositories must be nonempty')
    names = set()
    changes = 0
    for repo in repositories:
        obj(repo, ('name', 'base', 'head', 'role'), 'repository')
        name = repo['name']
        require(isinstance(name, str) and NAME.fullmatch(name) and name not in names, 'invalid or duplicate repository name')
        names.add(name)
        sha(repo['base'], f'{name} base')
        sha(repo['head'], f'{name} head')
        choice(repo['role'], ('change', 'context'), f'{name} role')
        require(repo['role'] != 'context' or repo['base'] == repo['head'], f'{name} context revisions differ')
        changes += repo['role'] == 'change'
        if 'project' in repo:
            string(repo['project'], f'{name} project')
    require(changes > 0, 'at least one changed repository is required')
    manifest_scope(report, manifest_lock)
    summary = obj(report['summary'], ('problem', 'change', 'effect'), 'summary')
    for key in ('problem', 'change', 'effect'):
        string(summary[key], 'summary ' + key)
    require(isinstance(report['walkthrough'], list), 'walkthrough must be a list')
    for item in report['walkthrough']:
        obj(item, ('repository', 'paths', 'change', 'effect'), 'walkthrough item')
        require(item['repository'] in names, 'walkthrough repository is not listed')
        require(isinstance(item['paths'], list), 'walkthrough paths must be a list')
        for value in item['paths']:
            path(value, 'walkthrough path')
        string(item['change'], 'walkthrough change')
        string(item['effect'], 'walkthrough effect')
    require(isinstance(report['findings'], list), 'findings must be a list')
    finding_ids = set()
    for item in report['findings']:
        obj(item, ('id', 'title', 'severity', 'repository', 'path', 'line', 'trigger', 'consequence',
                   'evidence', 'suggested_correction', 'validation_status', 'materiality', 'origin'), 'finding')
        identifier = string(item['id'], 'finding id')
        require(identifier not in finding_ids, 'duplicate finding id')
        finding_ids.add(identifier)
        string(item['title'], 'finding title')
        choice(item['severity'], ('P0', 'P1', 'P2', 'P3'), 'finding severity')
        require(item['repository'] in names, 'finding repository is not listed')
        path(item['path'], 'finding path')
        require(type(item['line']) is int and item['line'] > 0, 'finding line must be positive')
        for key in ('trigger', 'consequence', 'suggested_correction'):
            require(isinstance(item[key], str), f'finding {key} must be text')
        strings(item['evidence'], 'finding evidence')
        choice(item['validation_status'], ('confirmed', 'unresolved'), 'finding validation status')
        choice(item['materiality'], ('consequential', 'verification_gap', 'low_value', 'unresolved'), 'finding materiality')
        choice(item['origin'], ('CE', 'integration', 'both', 'analyzer'), 'finding origin')
        if item['validation_status'] == 'confirmed' and item['materiality'] == 'consequential':
            string(item['trigger'], 'confirmed finding trigger')
            string(item['consequence'], 'confirmed finding consequence')
            require(item['evidence'], 'confirmed finding requires source evidence')
    require(isinstance(report['checks'], list), 'checks must be a list')
    check_ids = set()
    for item in report['checks']:
        obj(item, ('id', 'name', 'status', 'required', 'reason', 'evidence'), 'check')
        identifier = string(item['id'], 'check id')
        require(identifier not in check_ids, 'duplicate check id')
        check_ids.add(identifier)
        string(item['name'], 'check name')
        choice(item['status'], ('pass', 'fail', 'warning', 'unavailable', 'not_applicable'), 'check status')
        require(type(item['required']) is bool, 'check required must be boolean')
        string(item['reason'], 'check reason')
        strings(item['evidence'], 'check evidence', item['status'] == 'pass' or identifier == 'docs')
    qa = obj(report['qa_runbook'], ('setup', 'steps', 'negative_cases', 'cleanup', 'execution_status', 'results'), 'QA runbook')
    for key in ('setup', 'cleanup', 'results'):
        strings(qa[key], 'QA ' + key)
    for key in ('steps', 'negative_cases'):
        require(isinstance(qa[key], list), f'QA {key} must be a list')
        for step in qa[key]:
            obj(step, ('action', 'expected', 'evidence_to_capture'), 'QA step')
            for field in ('action', 'expected', 'evidence_to_capture'):
                string(step[field], 'QA ' + field)
    choice(qa['execution_status'], ('proposed', 'partially_run', 'verified'), 'QA execution status')
    require(qa['execution_status'] != 'verified' or qa['results'], 'verified QA requires results')
    require(report['status'] != 'complete' or qa['steps'], 'complete review requires an executable QA step')
    require(isinstance(report['diagrams'], list), 'diagrams must be a list')
    for item in report['diagrams']:
        obj(item, ('kind', 'title', 'source', 'evidence'), 'diagram')
        choice(item['kind'], ('sequence', 'dbml'), 'diagram kind')
        string(item['title'], 'diagram title')
        string(item['source'], 'diagram source')
        strings(item['evidence'], 'diagram evidence', True)
    notes = obj(report['diagram_notes'], ('sequence', 'dbml'), 'diagram notes')
    string(notes['sequence'], 'sequence applicability')
    string(notes['dbml'], 'DBML applicability')
    strings(report['coverage_limits'], 'coverage limits')
    if report['status'] in ('degraded', 'failed'):
        require(report['coverage_limits'], 'incomplete review requires explicit coverage limits')
    choice(report['integration_status'], ('complete', 'degraded', 'failed', 'not_applicable'), 'integration status')
    if report['integration_status'] in ('degraded', 'failed'):
        require(report['coverage_limits'], 'incomplete integration requires explicit coverage limits')
    if report['integration_status'] == 'not_applicable':
        string(report.get('integration_skip_reason'), 'integration skip reason')
        require(changes < 2, 'multiple changed repositories require independent contract review')
        require(integration_receipt is None, 'an executed contract review cannot be declared inapplicable')
    if report['status'] == 'complete':
        require(report['integration_status'] in ('complete', 'not_applicable'),
                'complete report cannot omit a required review stage')
        receipt_scope(ce_receipt, scope, 'CE receipt')
        coverage = obj(ce_receipt.get('coverage'), ('depth',), 'CE coverage')
        choice(coverage['depth'], ('lite', 'focused', 'full'), 'CE depth')
        strings(ce_receipt.get('reviewers'), 'CE reviewers', True)
        if report['integration_status'] == 'complete':
            receipt_scope(integration_receipt, scope, 'integration receipt')
            require(isinstance(integration_receipt.get('findings'), list), 'integration receipt findings must be a list')
    finding_dispositions(report, ce_receipt, integration_receipt)
    return report


def recommendation(report, ce_receipt=None, integration_receipt=None, manifest_lock=None):
    validate_report(report, ce_receipt, integration_receipt, manifest_lock)
    reasons = []
    for finding in report['findings']:
        if (finding['validation_status'] == 'confirmed' and finding['materiality'] == 'consequential'
                and finding['severity'] in ('P0', 'P1', 'P2')):
            reasons.append(f"Confirmed consequential {finding['severity']} finding: {finding['id']}")
    for check in report['checks']:
        if check['required'] and check['status'] == 'fail':
            reasons.append(f"Required check failed: {check['name']}")
    if reasons:
        return {'status': 'hold', 'reasons': reasons}
    if report['status'] != 'complete':
        reasons.append(f"Review status: {report['status']}")
    if report['integration_status'] in ('degraded', 'failed'):
        reasons.append(f"Integration status: {report['integration_status']}")
    for check in report['checks']:
        if check['required'] and check['status'] in ('warning', 'unavailable', 'not_applicable'):
            reasons.append(f"Required check {check['status']}: {check['name']}")
    for finding in report['findings']:
        if finding['validation_status'] == 'unresolved' and finding['materiality'] in ('consequential', 'verification_gap', 'unresolved'):
            reasons.append(f"Material unresolved finding: {finding['id']}")
    return {'status': 'incomplete' if reasons else 'pass', 'reasons': reasons}


def data(value):
    value = html.escape(str(value), quote=True)
    value = MARKDOWN.sub(r'\\\1', value)
    return QUICK_ACTION.sub(lambda match: match.group(1) + '&#47;' + match.group(2), value)


def fenced(source, language):
    # Fenced text is already data; HTML escaping would break Mermaid arrows
    # and DBML quoted identifiers. Use a longer fence to prevent termination.
    source = QUICK_ACTION.sub(lambda match: match.group(1) + '&#47;' + match.group(2), source)
    longest = max((len(run) for run in re.findall(r'`+', source)), default=0)
    fence = '`' * max(3, longest + 1)
    return f'{fence}{language}\n{source}\n{fence}'


def render_report(report, ce_receipt=None, integration_receipt=None, manifest_lock=None):
    decision = recommendation(report, ce_receipt, integration_receipt, manifest_lock)
    lines = ['# Cross-repository review', '', '## Summary', '',
             f"**Intent:** {data(report['intent'])}", '',
             f"**Problem:** {data(report['summary']['problem'])}", '',
             f"**Change:** {data(report['summary']['change'])}", '',
             f"**Effect:** {data(report['summary']['effect'])}", '',
             f"**Advisory recommendation:** {decision['status']}",
             'This is advisory review evidence, not merge permission or a platform gate.']
    lines.extend(f'- {data(reason)}' for reason in decision['reasons'])
    lines += ['', '## Scope and coverage', '',
              f"Composite base: `{report['source_scope']['base']}`; head: `{report['source_scope']['head_sha']}`.",
              f"Review: {report['status']}; integration: {report['integration_status']}."]
    for repo in report['repositories']:
        lines.append(f"- {data(repo['name'])} ({repo['role']}): `{repo['base']}` → `{repo['head']}`")
    if report['integration_status'] == 'not_applicable':
        lines.append(f"Integration skip: {data(report['integration_skip_reason'])}")
    lines += [f"- Coverage limit: {data(limit)}" for limit in report['coverage_limits']]
    lines += ['', '## Walkthrough', '']
    if not report['walkthrough']:
        lines.append('No walkthrough entries supplied.')
    for entry in report['walkthrough']:
        paths = ', '.join(data(path) for path in entry['paths']) or '(no paths listed)'
        lines.append(f"- **{data(entry['repository'])}** ({paths}): {data(entry['change'])} Effect: {data(entry['effect'])}")
    lines += ['', '## Advisory checks', '']
    if not report['checks']:
        lines.append('No checks supplied.')
    for check in report['checks']:
        lines.append(f"- **{data(check['name'])}** [{check['status']}; required: {str(check['required']).lower()}]: {data(check['reason'])}")
        lines.extend(f"  - Evidence: {data(evidence)}" for evidence in check['evidence'])
    qa = report['qa_runbook']
    lines += ['', '## QA Runbook', '', f"Execution status: **{qa['execution_status']}**.", '']
    for key, heading in (('setup', 'Setup'), ('steps', 'Steps'), ('negative_cases', 'Negative cases'), ('cleanup', 'Cleanup'), ('results', 'Results')):
        lines += [f'### {heading}', '']
        for item in qa[key]:
            if isinstance(item, dict):
                lines.append(f"- {data(item['action'])} → {data(item['expected'])}; capture: {data(item['evidence_to_capture'])}")
            else:
                lines.append(f'- {data(item)}')
        if not qa[key]:
            lines.append('None supplied.')
        lines.append('')
    decisions = [item for item in report['finding_dispositions'] if item['action'] != 'retained']
    if decisions:
        lines += ['## Dispositioned review concerns', '']
        for item in decisions:
            receipt = ce_receipt if item['stage'] == 'ce' else integration_receipt
            key = '#' if item['stage'] == 'ce' else 'id'
            source = next(value for value in receipt['findings'] if str(value[key]) == item['source_id'])
            lines.append(f"- {data(item['stage'])}/{data(item['source_id'])} ({item['action']}; source {source['severity']}): {data(item['reason'])}")
            lines.extend(f"  - Evidence: {data(value)}" for value in item['evidence'])
        lines.append('')
    lines += ['## Diagrams', '', f"Sequence applicability: {data(report['diagram_notes']['sequence'])}",
              f"DBML applicability: {data(report['diagram_notes']['dbml'])}", '']
    for diagram in report['diagrams']:
        lines += [f"### {data(diagram['title'])}", '',
                  fenced(diagram['source'], 'mermaid' if diagram['kind'] == 'sequence' else 'dbml'), '',
                  'Source evidence: ' + ', '.join(data(item) for item in diagram['evidence']), '']
    lines += ['## Findings', '']
    if not report['findings']:
        lines.append('No findings supplied.')
    for finding in report['findings']:
        lines += [f"### {data(finding['id'])}: {data(finding['title'])}", '',
                  f"{finding['severity']} · {data(finding['validation_status'])} · {data(finding['materiality'])} · {data(finding['origin'])}", '',
                  f"Location: {data(finding['repository'])}/{data(finding['path'])}:{finding['line']}", '',
                  f"Trigger: {data(finding['trigger'])}", '', f"Consequence: {data(finding['consequence'])}", '',
                  f"Correction: {data(finding['suggested_correction'])}"]
        lines.extend(f"- Evidence: {data(item)}" for item in finding['evidence'])
        lines.append('')
    return '\n'.join(lines).rstrip() + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--report', required=True, type=Path)
    parser.add_argument('--ce-receipt', type=Path)
    parser.add_argument('--integration-receipt', type=Path)
    parser.add_argument('--manifest-lock', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    ce = json.loads(args.ce_receipt.read_text()) if args.ce_receipt else None
    integration = json.loads(args.integration_receipt.read_text()) if args.integration_receipt else None
    rendered = render_report(report, ce, integration, json.loads(args.manifest_lock.read_text()))
    args.output.write_text(rendered)


if __name__ == '__main__':
    main()
