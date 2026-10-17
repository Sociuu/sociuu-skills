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


def coverage_inventory(receipt, name, fields):
    inventory = obj(receipt.get(name), ('rows',), name)
    rows = inventory['rows']
    require(isinstance(rows, list), f'{name} rows must be a list')
    if rows:
        for row in rows:
            obj(row, (*fields, 'evidence', 'base_head_attribution'), name + ' row')
            for field in fields + ('base_head_attribution',):
                string(row[field], name + ' ' + field)
            strings(row['evidence'], name + ' evidence', True)
        require('not_applicable_reason' not in inventory and 'not_applicable_evidence' not in inventory,
                f'{name} cannot have rows and a not-applicable claim')
    else:
        string(inventory.get('not_applicable_reason'), name + ' not-applicable reason')
        strings(inventory.get('not_applicable_evidence'), name + ' not-applicable evidence', True)


def contract_review_applicability(report, changes):
    review = obj(report.get('contract_review'), ('required', 'reason', 'evidence'), 'contract review applicability')
    require(type(review['required']) is bool, 'contract review required must be boolean')
    string(review['reason'], 'contract review applicability reason')
    strings(review['evidence'], 'contract review applicability evidence', True)
    require(changes < 2 or review['required'], 'multiple changed repositories require independent contract review')
    if review['required']:
        require(report['integration_status'] != 'not_applicable',
                'required contract review cannot be declared inapplicable')


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


def source_claims(report, claims, label):
    require(isinstance(claims, list), label + 's must be a list')
    repositories = {repo['name'] for repo in report['repositories']}
    identifiers = set()
    for concern in claims:
        obj(concern, ('id', 'title', 'severity', 'repository', 'path', 'line', 'trigger', 'consequence',
                      'evidence', 'suggested_correction', 'validation_status', 'materiality'), label)
        identifier = string(concern['id'], label + ' ID')
        require(identifier not in identifiers, 'duplicate ' + label + ' ID')
        identifiers.add(identifier)
        for field in ('title', 'trigger', 'consequence', 'suggested_correction'):
            string(concern[field], label + ' ' + field)
        choice(concern['severity'], ('P0', 'P1', 'P2', 'P3'), label + ' severity')
        choice(concern['validation_status'], ('confirmed', 'unresolved'), label + ' validation')
        choice(concern['materiality'], ('consequential', 'verification_gap', 'low_value', 'unresolved'),
               label + ' materiality')
        require(concern['repository'] in repositories, label + ' repository is not listed')
        path(concern['path'], label + ' path')
        require(type(concern['line']) is int and concern['line'] > 0, label + ' line must be positive')
        strings(concern['evidence'], label + ' evidence', True)
    return identifiers


def inventory_concerns(report, receipt):
    """Check declared row-to-claim links, not the semantic absence of concerns."""
    if report['version'] < 3 or receipt is None:
        return []
    obj(receipt, ('status',), 'integration receipt')
    concerns = receipt.get('inventory_concerns', [] if receipt['status'] != 'complete' else None)
    identifiers = source_claims(report, concerns, 'inventory concern')
    linked = set()
    for name in ('boundary_checks', 'credential_policy_matrix', 'optional_field_matrix'):
        if name not in receipt:
            continue
        inventory = obj(receipt[name], ('rows',), name)
        require(isinstance(inventory['rows'], list), name + ' rows must be a list')
        if name == 'optional_field_matrix':
            coverage_inventory(receipt, name, ('field_group', 'saved_input', 'omitted_result', 'explicit_clear_result'))
        for row in inventory['rows']:
            obj(row, ('concern_ids', 'evidence'), name + ' concern links')
            strings(row['evidence'], name + ' evidence', True)
            refs = strings(row['concern_ids'], name + ' concern IDs')
            require(len(refs) == len(set(refs)), 'duplicate inventory concern reference')
            require(set(refs) <= identifiers, 'unknown inventory concern reference')
            linked.update(refs)
            if name == 'optional_field_matrix':
                strings(row.get('caller_evidence'), name + ' caller evidence', True)
    require(linked == identifiers, 'unlinked inventory concern')
    return concerns


def finding_dispositions(report, ce_receipt, integration_receipt, analyzer_receipt=None):
    raw = {}
    concerns = inventory_concerns(report, integration_receipt)
    if analyzer_receipt is not None:
        require(report['version'] == 3, 'analyzer candidate receipts require version 3')
        obj(analyzer_receipt, ('status', 'findings'), 'analyzer candidate receipt')
        require(report['status'] != 'complete' or analyzer_receipt['status'] == 'complete',
                'complete report requires complete analyzer candidate receipt')
        source_claims(report, analyzer_receipt['findings'], 'analyzer candidate')
    for stage, receipt, id_key in (('ce', ce_receipt, '#'), ('integration', integration_receipt, 'id'),
                                   ('inventory', integration_receipt, 'id'), ('analyzer', analyzer_receipt, 'id')):
        if receipt is None:
            continue
        obj(receipt, ('status',), stage + ' receipt')
        choice(receipt['status'], ('complete', 'degraded', 'failed', 'skipped'), stage + ' receipt status')
        findings = concerns if stage == 'inventory' else receipt.get('findings', [] if receipt['status'] != 'complete' else None)
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
        choice(item['stage'], ('ce', 'integration', 'inventory', 'analyzer') if report['version'] >= 3 else ('ce', 'integration'),
               'disposition stage')
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
            retained[identifier].add('integration' if item['stage'] == 'inventory' else item['stage'])
            source, destination = raw[key], reported[identifier]
            source_materiality = source.get('materiality', 'consequential' if source['severity'] != 'P3' else None)
            if report['version'] == 3:
                source_materiality = source.get('materiality', source.get('finding_type', source_materiality))
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
                      'both': {'ce', 'integration'}, 'analyzer': {'analyzer'} if report['version'] == 3 else set()}[finding['origin']]
            require(needed <= retained[finding['id']], 'reported finding lacks its declared review provenance')
    return raw


def calibration_closure(report, raw, receipt):
    expected = {stage + '/' + identifier for stage, identifier in raw}
    checks = [check for check in report['checks'] if check['id'] == 'calibration']
    require(len(checks) == 1, 'v3 requires exactly one calibration check or evidenced zero-claim skip')
    check = checks[0]
    if expected:
        require(check['required'], 'calibration check must be required for source claims')
        require(check['status'] != 'not_applicable', 'source claims cannot skip calibration')
    elif receipt is None and check['status'] == 'not_applicable':
        require(not check['required'], 'zero-claim calibration skip must be nonrequired')
        strings(check['evidence'], 'zero-claim calibration skip evidence', True)
        return
    require(report['status'] != 'complete' or check['status'] == 'pass',
            'complete report requires passed calibration closure')
    if receipt is None:
        require(check['status'] != 'pass', 'passed calibration requires original calibration receipt')
        return
    obj(receipt, ('scope', 'status', 'groups'), 'calibration receipt')
    actual = obj(receipt['scope'], ('base', 'head_sha'), 'calibration scope')
    require(all(actual[key] == report['source_scope'][key] for key in ('base', 'head_sha')),
            'calibration receipt scope differs')
    choice(receipt['status'], ('complete', 'degraded', 'failed'), 'calibration receipt status')
    require(receipt['status'] == 'complete' or (report['status'] != 'complete' and check['status'] != 'pass'),
            'failed or incomplete calibration cannot establish closure')
    require(isinstance(receipt['groups'], list), 'calibration groups must be a list')
    mapped = {item['stage'] + '/' + item['source_id']: item for item in report['finding_dispositions']}
    findings = {finding['id']: finding for finding in report['findings']}
    accounted = set()
    for group in receipt['groups']:
        obj(group, ('input_ids', 'severity', 'finding_type', 'validation_status', 'actor', 'preconditions',
                    'final_effect', 'recovery', 'evidence', 'missing_evidence'), 'calibration group')
        inputs = strings(group['input_ids'], 'calibration input IDs', True)
        require(len(inputs) == len(set(inputs)) and not accounted.intersection(inputs),
                'duplicate calibration input accounting')
        require(set(inputs) <= expected, 'unknown calibration input')
        accounted.update(inputs)
        choice(group['severity'], ('P0', 'P1', 'P2', 'P3'), 'calibration severity')
        choice(group['finding_type'], ('consequential', 'verification_gap', 'low_value', 'unresolved'),
               'calibration finding type')
        choice(group['validation_status'], ('confirmed', 'unresolved', 'rejected'), 'calibration validation')
        for field in ('actor', 'final_effect', 'recovery'):
            string(group[field], 'calibration ' + field)
        strings(group['preconditions'], 'calibration preconditions', True)
        strings(group['evidence'], 'calibration source evidence', True)
        strings(group['missing_evidence'], 'calibration missing evidence', group['validation_status'] == 'unresolved')
        destinations = set()
        for identifier in inputs:
            item = mapped[identifier]
            if item['action'] == 'rejected':
                continue
            destinations.add(item['finding_id'])
            finding = findings[item['finding_id']]
            changed = (group['severity'] != finding['severity'] or group['finding_type'] != finding['materiality'] or
                       group['validation_status'] != finding['validation_status'])
            require(not changed or item['action'] == 'reclassified',
                    'calibration disagreement requires explicit reclassification evidence')
        require(len(destinations) <= 1, 'calibration causal group must map to one final finding')
    require(receipt['status'] != 'complete' or accounted == expected,
            'source claims are missing from calibration input accounting')


def validate_report(report, ce_receipt=None, integration_receipt=None, manifest_lock=None, calibration_receipt=None, analyzer_receipt=None):
    obj(report, ('version', 'status', 'source_scope', 'repositories', 'intent', 'summary',
                 'walkthrough', 'findings', 'checks', 'qa_runbook', 'diagrams', 'diagram_notes',
                 'coverage_limits', 'integration_status', 'finding_dispositions'), 'report')
    require(type(report['version']) is int and report['version'] in (1, 2, 3), 'unsupported report version')
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
    if report['version'] >= 2:
        calibration = [item for item in report['checks'] if item['id'] == 'calibration']
        if report['findings']:
            require(len(calibration) == 1, 'retained findings require exactly one calibration check')
            require(calibration[0]['required'], 'calibration check must be required for retained findings')
            require(report['status'] != 'complete' or calibration[0]['status'] == 'pass',
                    'complete report requires passed calibration')
        if report['status'] == 'complete' and calibration:
            require(calibration[0]['status'] in ('pass', 'not_applicable'),
                    'complete report cannot retain failed or incomplete calibration')
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
    if report['version'] >= 2:
        contract_review_applicability(report, changes)
    if report['integration_status'] in ('degraded', 'failed'):
        require(report['coverage_limits'], 'incomplete integration requires explicit coverage limits')
    if report['integration_status'] == 'not_applicable':
        string(report.get('integration_skip_reason'), 'integration skip reason')
        require(changes < 2, 'multiple changed repositories require independent contract review')
        require(integration_receipt is None, 'an executed contract review cannot be declared inapplicable')
    if report['version'] >= 2 and report['integration_status'] == 'complete':
        receipt_scope(integration_receipt, scope, 'integration receipt')
        require(isinstance(integration_receipt.get('findings'), list), 'integration receipt findings must be a list')
        coverage_inventory(integration_receipt, 'boundary_checks',
                           ('input_branch', 'validation_transformation', 'destination', 'observed_result'))
        coverage_inventory(integration_receipt, 'credential_policy_matrix',
                           ('representation', 'source', 'transformation', 'destination', 'policy', 'observed_result'))
    if report['status'] == 'complete':
        require(report['integration_status'] in ('complete', 'not_applicable'),
                'complete report cannot omit a required review stage')
        receipt_scope(ce_receipt, scope, 'CE receipt')
        coverage = obj(ce_receipt.get('coverage'), ('depth',), 'CE coverage')
        choice(coverage['depth'], ('lite', 'focused', 'full'), 'CE depth')
        strings(ce_receipt.get('reviewers'), 'CE reviewers', True)
        if report['version'] == 1 and report['integration_status'] == 'complete':
            receipt_scope(integration_receipt, scope, 'integration receipt')
            require(isinstance(integration_receipt.get('findings'), list), 'integration receipt findings must be a list')
    raw = finding_dispositions(report, ce_receipt, integration_receipt, analyzer_receipt)
    if report['version'] == 3:
        calibration_closure(report, raw, calibration_receipt)
    return report


def recommendation(report, ce_receipt=None, integration_receipt=None, manifest_lock=None, calibration_receipt=None, analyzer_receipt=None):
    validate_report(report, ce_receipt, integration_receipt, manifest_lock, calibration_receipt, analyzer_receipt)
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
    if report['version'] == 1:
        reasons.append('Legacy v1 report lacks the contract applicability and coverage inventory contract')
    if report['version'] == 2:
        reasons.append('Legacy v2 report lacks inventory concern closure and original calibration input accounting')
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


def render_report(report, ce_receipt=None, integration_receipt=None, manifest_lock=None, calibration_receipt=None, analyzer_receipt=None):
    decision = recommendation(report, ce_receipt, integration_receipt, manifest_lock, calibration_receipt, analyzer_receipt)
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
    if report['version'] >= 2:
        applicability = report['contract_review']
        lines.append(f"Contract review required: {str(applicability['required']).lower()}; reason: {data(applicability['reason'])}")
        lines.extend(f"- Applicability evidence: {data(item)}" for item in applicability['evidence'])
    for repo in report['repositories']:
        lines.append(f"- {data(repo['name'])} ({repo['role']}): `{repo['base']}` → `{repo['head']}`")
    if report['integration_status'] == 'not_applicable':
        lines.append(f"Integration skip: {data(report['integration_skip_reason'])}")
    lines += [f"- Coverage limit: {data(limit)}" for limit in report['coverage_limits']]
    if report['version'] >= 2 and report['integration_status'] == 'complete' and integration_receipt is not None:
        lines += ['', '## Contract review coverage', '']
        inventories = [
                ('boundary_checks', 'Boundary checks', ('input_branch', 'validation_transformation', 'destination', 'observed_result')),
                ('credential_policy_matrix', 'Credential policy matrix', ('representation', 'source', 'transformation', 'destination', 'policy', 'observed_result'))]
        if report['version'] == 3 and 'optional_field_matrix' in integration_receipt:
            inventories.append(('optional_field_matrix', 'Optional field matrix',
                                ('field_group', 'saved_input', 'omitted_result', 'explicit_clear_result')))
        for name, heading, fields in inventories:
            inventory = integration_receipt[name]
            lines += [f'### {heading}', '']
            if inventory['rows']:
                for row in inventory['rows']:
                    lines.append('- ' + '; '.join(f'{field}: {data(row[field])}' for field in fields))
                    lines.append(f"  - Base/head attribution: {data(row['base_head_attribution'])}")
                    lines.extend(f'  - Evidence: {data(item)}' for item in row['evidence'])
                    if report['version'] == 3:
                        lines.append('  - Concern IDs: ' + (', '.join(data(item) for item in row['concern_ids']) or 'None declared'))
            else:
                lines.append(f"Not applicable: {data(inventory['not_applicable_reason'])}")
                lines.extend(f"- Evidence: {data(item)}" for item in inventory['not_applicable_evidence'])
            lines.append('')
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
    decisions = [item for item in report['finding_dispositions'] if report['version'] == 3 or item['action'] != 'retained']
    if decisions:
        lines += ['## Dispositioned review concerns', '']
        for item in decisions:
            receipt = {'ce': ce_receipt, 'analyzer': analyzer_receipt}.get(item['stage'], integration_receipt)
            key = '#' if item['stage'] == 'ce' else 'id'
            collection = receipt['inventory_concerns'] if item['stage'] == 'inventory' else receipt['findings']
            source = next(value for value in collection if str(value[key]) == item['source_id'])
            lines.append(f"- {data(item['stage'])}/{data(item['source_id'])} ({item['action']}; source {source['severity']}): {data(item['reason'])}")
            if 'finding_id' in item:
                lines.append(f"  - Final finding: {data(item['finding_id'])}")
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
    parser.add_argument('--calibration-receipt', type=Path)
    parser.add_argument('--analyzer-receipt', type=Path)
    parser.add_argument('--manifest-lock', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    ce = json.loads(args.ce_receipt.read_text()) if args.ce_receipt else None
    integration = json.loads(args.integration_receipt.read_text()) if args.integration_receipt else None
    calibration = json.loads(args.calibration_receipt.read_text()) if args.calibration_receipt else None
    analyzer = json.loads(args.analyzer_receipt.read_text()) if args.analyzer_receipt else None
    rendered = render_report(report, ce, integration, json.loads(args.manifest_lock.read_text()), calibration, analyzer)
    args.output.write_text(rendered)


if __name__ == '__main__':
    main()
