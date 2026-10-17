#!/usr/bin/env python3
"""Bounded GitLab intake and advisory note adapter using managed glab auth."""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile
from urllib.parse import quote

from report import render_report, SHA, require


MARKER = '<!-- sociuu-cross-repo-review:v1 -->'
QUICK_ACTION = re.compile(r'^\s*/[A-Za-z]', re.MULTILINE)
PROJECT = re.compile(r'(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_.-]+\Z')


def project_id(value):
    require(isinstance(value, str) and bool(PROJECT.fullmatch(value)) and
            all(part not in ('.', '..') for part in value.split('/')), 'invalid GitLab project')
    return quote(value, safe='')


def iid(value):
    require(type(value) is int and value > 0 or
            isinstance(value, str) and value.isdecimal() and int(value) > 0,
            'MR IID must be positive')
    return int(value)


def api(endpoint, method='GET', body=None):
    command = ['glab', 'api', endpoint]
    if method != 'GET':
        command += ['--method', method]
    if body is not None:
        with tempfile.TemporaryDirectory(prefix='sociuu-review-api-') as directory:
            body_file = Path(directory) / 'body.json'
            body_file.write_text(json.dumps({'body': body}))
            command += ['--input', str(body_file)]
            result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=60)
    else:
        result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=60)
    if result.returncode:
        raise RuntimeError(f'glab api {method} {endpoint} failed: {result.stderr.strip()}')
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError(f'glab api {endpoint} returned invalid JSON') from exc


def path(project, mr):
    return f'/projects/{project_id(project)}/merge_requests/{iid(mr)}'


def mr_snapshot(project, mr):
    result = api(path(project, mr))
    require(isinstance(result, dict), 'MR metadata unavailable')
    refs = result.get('diff_refs') or {}
    base, head = refs.get('base_sha'), refs.get('head_sha')
    require(isinstance(base, str) and SHA.fullmatch(base) and
            isinstance(head, str) and SHA.fullmatch(head), 'MR diff refs unavailable')
    require(result.get('state') in ('opened', 'closed', 'merged'), 'MR state unavailable')
    return result


def paginate(endpoint):
    all_items = []
    page = 1
    while True:
        separator = '&' if '?' in endpoint else '?'
        items = api(f'{endpoint}{separator}per_page=100&page={page}')
        require(isinstance(items, list), f'{endpoint} response must be a list')
        all_items.extend(items)
        if len(items) < 100:
            return all_items
        page += 1


def inspect(project, mr):
    metadata = mr_snapshot(project, mr)
    endpoint = path(project, mr)
    return {'project': project, 'iid': iid(mr), 'state': metadata['state'],
            'base_sha': metadata['diff_refs']['base_sha'],
            'head_sha': metadata['diff_refs']['head_sha'],
            'metadata': metadata,
            'notes': paginate(endpoint + '/notes'),
            'diffs': paginate(endpoint + '/diffs')}


def event_target(event):
    require(isinstance(event, dict) and event.get('object_kind') == 'merge_request',
            'event must be a merge_request webhook')
    project = event.get('project')
    attrs = event.get('object_attributes')
    require(isinstance(project, dict) and isinstance(attrs, dict), 'invalid MR event')
    value = project.get('path_with_namespace') or project.get('id')
    require(value is not None, 'event project unavailable')
    value = str(value)
    project_id(value)
    return value, iid(attrs.get('iid'))


def current_revisions(project, mr, expected, opened=True):
    current = mr_snapshot(project, mr)
    refs = current['diff_refs']
    require(not opened or current['state'] == 'opened', f'{project}!{mr} is not opened')
    require(refs['base_sha'] == expected['base'] and refs['head_sha'] == expected['head'],
            f'{project}!{mr} source revisions changed')
    require(current.get('sha') == refs['head_sha'],
            f'{project}!{mr} diff refs are pending for the latest source revision')
    return current


def parse_companion(value):
    require('!' in value, 'companion must be PROJECT!IID')
    project, number = value.rsplit('!', 1)
    project_id(project)
    return project, iid(number)


def mapped_revisions(report, project, mr, companions):
    mappings = {(project, iid(mr)): None}
    for item in companions:
        target = parse_companion(item)
        require(target not in mappings, 'duplicate companion MR')
        mappings[target] = None
    changed = [repo for repo in report['repositories'] if repo['role'] == 'change']
    projects = [repo.get('project') for repo in changed]
    require(all(projects), 'every changed repository needs a project mapping')
    require(len(set(projects)) == len(projects), 'changed repository projects must be unique')
    require(set(projects) == {name for name, _ in mappings},
            'changed repositories must match target and named companion MRs')
    for repo in changed:
        project_id(repo['project'])
        key = next(key for key in mappings if key[0] == repo['project'])
        mappings[key] = {'base': repo['base'], 'head': repo['head']}
    return mappings


def note_candidates(notes):
    return [note for note in notes if isinstance(note, dict) and
            isinstance(note.get('body'), str) and
            note['body'].startswith(MARKER + '\n# Cross-repository review\n')]


def publish(args):
    report = json.loads(args.report.read_text())
    if args.publish:
        require(isinstance(report, dict) and report.get('version') == 3,
                'explicit publication requires report version 3')
    ce = json.loads(args.ce_receipt.read_text()) if args.ce_receipt else None
    integration = json.loads(args.integration_receipt.read_text()) if args.integration_receipt else None
    calibration = json.loads(args.calibration_receipt.read_text()) if args.calibration_receipt else None
    analyzer = json.loads(args.analyzer_receipt.read_text()) if args.analyzer_receipt else None
    manifest_lock = json.loads(args.manifest_lock.read_text())
    rendered = render_report(report, ce, integration, manifest_lock, calibration, analyzer)
    require(MARKER not in rendered, 'report contains reserved publication marker')
    body = MARKER + '\n' + rendered
    require(body.count(MARKER) == 1 and not QUICK_ACTION.search(body),
            'review contains a GitLab quick action')
    mappings = mapped_revisions(report, args.project, args.mr, args.companion)
    for (project, mr), expected in mappings.items():
        current_revisions(project, mr, expected)
    args.output.write_text(body)
    if not args.publish:
        return
    endpoint = path(args.project, args.mr) + '/notes'
    notes = paginate(endpoint)
    matches = note_candidates(notes)
    require(len(matches) <= 1, 'multiple marked review notes require reconciliation')
    author = api('/user')
    require(isinstance(author, dict) and isinstance(author.get('id'), int),
            'current GitLab author unavailable')
    if matches:
        require(matches[0].get('author', {}).get('id') == author['id'],
                'marked review note belongs to another author')
    for (project, mr), expected in mappings.items():
        current_revisions(project, mr, expected)
    if matches and matches[0]['body'] == body:
        return
    method = 'PUT' if matches else 'POST'
    note_endpoint = endpoint + '/' + str(matches[0]['id']) if matches else endpoint
    written = api(note_endpoint, method=method, body=body)
    note_id = written.get('id') if isinstance(written, dict) else None
    require(isinstance(note_id, int) and note_id > 0,
            f'{method} returned no note ID; reconciliation required')
    try:
        readback = api(endpoint + '/' + str(note_id))
        require(isinstance(readback, dict) and readback.get('id') == note_id and
                readback.get('body') == body and readback.get('author', {}).get('id') == author['id'],
                f'note {note_id} readback differs; reconciliation required')
        for (project, mr), expected in mappings.items():
            current_revisions(project, mr, expected)
    except Exception as exc:
        raise RuntimeError(f'note {note_id} may have been written; reconciliation required: {exc}') from exc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    inspect_parser = commands.add_parser('inspect')
    inspect_parser.add_argument('--project', required=True)
    inspect_parser.add_argument('--mr', required=True)
    inspect_parser.add_argument('--output', required=True, type=Path)
    event_parser = commands.add_parser('event')
    event_parser.add_argument('--event', required=True, type=Path)
    event_parser.add_argument('--output', required=True, type=Path)
    publish_parser = commands.add_parser('publish')
    publish_parser.add_argument('--project', required=True)
    publish_parser.add_argument('--mr', required=True)
    publish_parser.add_argument('--report', required=True, type=Path)
    publish_parser.add_argument('--ce-receipt', type=Path)
    publish_parser.add_argument('--integration-receipt', type=Path)
    publish_parser.add_argument('--calibration-receipt', type=Path)
    publish_parser.add_argument('--analyzer-receipt', type=Path)
    publish_parser.add_argument('--manifest-lock', required=True, type=Path)
    publish_parser.add_argument('--companion', action='append', default=[], metavar='PROJECT!IID')
    publish_parser.add_argument('--output', required=True, type=Path)
    publish_parser.add_argument('--publish', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'inspect':
            args.output.write_text(json.dumps(inspect(args.project, args.mr), indent=2) + '\n')
        elif args.command == 'event':
            project, mr = event_target(json.loads(args.event.read_text()))
            args.output.write_text(json.dumps(inspect(project, mr), indent=2) + '\n')
        else:
            publish(args)
    except (ValueError, RuntimeError, OSError) as exc:
        parser.exit(1, f'gitlab adapter: {exc}\n')


if __name__ == '__main__':
    main()
