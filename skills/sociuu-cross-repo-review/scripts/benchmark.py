#!/usr/bin/env python3
"""Freeze a reviewer and its outputs before releasing historical references."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys


CASE_ID = re.compile(r'[A-Za-z0-9][A-Za-z0-9._-]{0,100}\Z')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def now():
    return datetime.now(timezone.utc).isoformat()


def read_json(path):
    return json.loads(path.read_text())


def write_new(path, data):
    with path.open('x') as stream:
        json.dump(data, stream, indent=2)
        stream.write('\n')


def git(tree, *args):
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update(GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_NOSYSTEM='1', GIT_OPTIONAL_LOCKS='0')
    result = subprocess.run(['git', '-C', str(tree), *args], env=env,
                            capture_output=True, text=True)
    if result.returncode:
        raise ValueError(f'packet Git check failed: {result.stderr.strip()}')
    return result.stdout.strip()


def candidate_state(roots):
    files = {}
    for item in roots:
        root = Path(item)
        if not root.exists():
            raise ValueError(f'candidate does not exist: {root}')
        paths = root.rglob('*') if root.is_dir() else [root]
        for path in sorted(paths):
            if {'.git', '__pycache__'} & set(path.parts):
                continue
            if path.is_symlink() and path.is_dir():
                raise ValueError(f'candidate directory symlink is not supported: {path}')
            if not path.is_file():
                continue
            files[str(path.absolute())] = {
                'sha256': digest(path.read_bytes()), 'mode': stat.S_IMODE(path.stat().st_mode),
                'link': os.readlink(path) if path.is_symlink() else None}
    if not files:
        raise ValueError('candidate contains no files')
    return files


def packet_state(case):
    if not isinstance(case, dict) or set(case) != {'id', 'tree', 'base', 'head'}:
        raise ValueError('each case requires exactly id, tree, base, head')
    if not isinstance(case['id'], str) or not CASE_ID.fullmatch(case['id']):
        raise ValueError('invalid case ID')
    tree = Path(case['tree'])
    if not tree.is_absolute() or not tree.is_dir():
        raise ValueError('case tree must be an existing absolute directory')
    for ref in ('base', 'head'):
        if not isinstance(case[ref], str) or not re.fullmatch(r'[0-9a-f]{40}|[0-9a-f]{64}', case[ref]):
            raise ValueError('case revisions must be full commit IDs')
        git(tree, 'cat-file', '-e', case[ref] + '^{commit}')
    if git(tree, 'rev-parse', 'HEAD') != case['head']:
        raise ValueError('packet HEAD differs from registered proposed revision')
    if git(tree, 'status', '--porcelain', '--untracked-files=all', '--ignored=matching'):
        raise ValueError('packet has modified or extra source files')
    if git(tree, 'remote'):
        raise ValueError('blind packets must have no remotes')
    ancestry = git(tree, 'rev-list', '--parents', '--all').splitlines()
    expected_ancestry = {case['head'] + ' ' + case['base'], case['base']}
    objects = git(tree, 'cat-file', '--batch-all-objects',
                  '--batch-check=%(objectname) %(objecttype)').splitlines()
    commits = {line.split()[0] for line in objects if line.endswith(' commit')}
    if set(ancestry) != expected_ancestry or commits != {case['base'], case['head']}:
        raise ValueError('blind packet must contain only its two synthetic commits')
    return {'base_tree': git(tree, 'rev-parse', case['base'] + '^{tree}'),
            'head_tree': git(tree, 'rev-parse', case['head'] + '^{tree}'),
            'refs': digest(git(tree, 'show-ref', '--head').encode())}


def register(directory, roots, cases_path, reference_sha256):
    if directory.exists():
        raise ValueError('run directory already exists')
    if not re.fullmatch(r'[0-9a-f]{64}', reference_sha256):
        raise ValueError('reference SHA256 must be a full lowercase digest')
    roots = [str(Path(root).absolute()) for root in roots]
    candidates = candidate_state(roots)
    cases = read_json(cases_path)
    if not isinstance(cases, list) or not cases:
        raise ValueError('cases must be a nonempty list')
    seen = set()
    packets = {}
    for case in cases:
        state = packet_state(case)
        if case['id'] in seen:
            raise ValueError('duplicate case ID')
        seen.add(case['id'])
        packets[case['id']] = state
    for source in [*roots, *(case['tree'] for case in cases)]:
        if directory.resolve().is_relative_to(Path(source).resolve()):
            raise ValueError('run artifacts must be outside candidate and source trees')
    directory.mkdir(parents=True, mode=0o700)
    (directory / 'frozen').mkdir(mode=0o700)
    write_new(directory / 'registration.json', {
        'version': 1, 'registered_at': now(), 'candidate_roots': roots,
        'candidate_files': candidates, 'cases': cases, 'packets': packets,
        'reference_sha256': reference_sha256})
    return {'status': 'registered', 'cases': len(cases), 'candidate_files': len(candidates)}


def verify(directory, require_all=False):
    record = read_json(directory / 'registration.json')
    if candidate_state(record['candidate_roots']) != record['candidate_files']:
        raise ValueError('candidate changed after registration')
    frozen = []
    for case in record['cases']:
        if packet_state(case) != record['packets'][case['id']]:
            raise ValueError(f'packet changed after registration: {case["id"]}')
        receipt_path = directory / 'frozen' / (case['id'] + '.receipt.json')
        report_path = directory / 'frozen' / (case['id'] + '.json')
        if not receipt_path.exists():
            if report_path.exists() or require_all:
                raise ValueError(f'case has no completed freeze: {case["id"]}')
            continue
        receipt = read_json(receipt_path)
        if receipt['sha256'] != digest(report_path.read_bytes()):
            raise ValueError(f'frozen output changed: {case["id"]}')
        for name, expected_hash in receipt.get('artifacts', {}).items():
            if name not in ('ce', 'integration'):
                raise ValueError('unknown frozen review artifact')
            artifact = directory / 'frozen' / f'{case["id"]}.{name}.json'
            if digest(artifact.read_bytes()) != expected_hash:
                raise ValueError(f'frozen review artifact changed: {case["id"]}/{name}')
        frozen.append(case['id'])
    reference = directory / 'reference.json'
    unsealed = directory / 'unsealed.json'
    if reference.exists() or unsealed.exists():
        if not reference.exists() or not unsealed.exists():
            raise ValueError('reference release is incomplete')
        expected_hash = read_json(unsealed)['reference_sha256']
        if expected_hash != record['reference_sha256'] or digest(reference.read_bytes()) != expected_hash:
            raise ValueError('released reference changed')
    return record, frozen


def freeze(directory, case_id, report_path, receipt_specs):
    record, frozen = verify(directory)
    if case_id not in {case['id'] for case in record['cases']}:
        raise ValueError('case is not registered')
    if case_id in frozen:
        raise ValueError('case output is already frozen')
    data = report_path.read_bytes()
    report = json.loads(data)
    if (not isinstance(report, dict) or report.get('status') not in
            ('complete', 'degraded', 'failed', 'skipped') or not isinstance(report.get('findings'), list)):
        raise ValueError('report requires explicit status and findings array')
    artifacts = {}
    parsed = {}
    for spec in receipt_specs:
        name, separator, path = spec.partition('=')
        if not separator or name not in ('ce', 'integration') or name in artifacts:
            raise ValueError('receipts use unique ce=PATH or integration=PATH arguments')
        artifacts[name] = Path(path).read_bytes()
        parsed[name] = json.loads(artifacts[name])
    case = next(case for case in record['cases'] if case['id'] == case_id)
    if report['status'] == 'complete':
        ce = parsed.get('ce', {})
        scope = ce.get('scope', {})
        if (ce.get('status') != 'complete' or not ce.get('reviewers') or
                ce.get('coverage', {}).get('depth') not in ('lite', 'focused', 'full') or
                scope.get('base') != case['base'] or scope.get('head_sha') != case['head']):
            raise ValueError('complete report requires a CE receipt for this exact packet')
        integration_status = report.get('integration_status')
        if integration_status == 'complete':
            integration = parsed.get('integration', {})
            integration_scope = integration.get('scope', {})
            if (integration.get('status') != 'complete' or not isinstance(integration.get('findings'), list) or
                    integration_scope.get('base') != case['base'] or integration_scope.get('head_sha') != case['head']):
                raise ValueError('completed integration pass requires its receipt')
        elif integration_status != 'not_applicable' or not report.get('integration_skip_reason'):
            raise ValueError('complete report must account for the integration pass')
    destination = directory / 'frozen' / (case_id + '.json')
    with destination.open('xb') as stream:
        stream.write(data)
    for name, content in artifacts.items():
        with (directory / 'frozen' / f'{case_id}.{name}.json').open('xb') as stream:
            stream.write(content)
    receipt = {'case': case_id, 'frozen_at': now(), 'status': report['status'],
               'sha256': digest(data), 'finding_count': len(report['findings']),
               'artifacts': {name: digest(content) for name, content in artifacts.items()}}
    write_new(directory / 'frozen' / (case_id + '.receipt.json'), receipt)
    return receipt


def unseal(directory, expected_path):
    record, frozen = verify(directory, require_all=True)
    if (directory / 'reference.json').exists() or (directory / 'unsealed.json').exists():
        raise ValueError('references are already unsealed')
    # The reference is first read only after every output and input is verified.
    data = expected_path.read_bytes()
    if digest(data) != record['reference_sha256']:
        raise ValueError('reference changed after registration')
    json.loads(data)
    with (directory / 'reference.json').open('xb') as stream:
        stream.write(data)
    receipt = {'unsealed_at': now(), 'reference_sha256': digest(data), 'frozen_cases': frozen}
    write_new(directory / 'unsealed.json', receipt)
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest='command', required=True)
    for name in ('register', 'freeze', 'verify', 'unseal'):
        sub = subparsers.add_parser(name)
        sub.add_argument('--directory', type=Path, required=True)
        if name == 'register':
            sub.add_argument('--candidate', action='append', required=True)
            sub.add_argument('--cases', type=Path, required=True)
            sub.add_argument('--reference-sha256', required=True)
        elif name == 'freeze':
            sub.add_argument('--case', required=True)
            sub.add_argument('--report', type=Path, required=True)
            sub.add_argument('--receipt', action='append', default=[])
        elif name == 'unseal':
            sub.add_argument('--expected', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'register':
            result = register(args.directory, args.candidate, args.cases, args.reference_sha256)
        elif args.command == 'freeze':
            result = freeze(args.directory, args.case, args.report, args.receipt)
        elif args.command == 'unseal':
            result = unseal(args.directory, args.expected)
        else:
            record, frozen = verify(args.directory)
            result = {'status': 'verified', 'frozen': len(frozen), 'cases': len(record['cases'])}
        print(json.dumps(result))
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f'benchmark: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
