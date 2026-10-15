#!/usr/bin/env python3
"""Build a two-commit, source-only snapshot for cross-repository review."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile


NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]*\Z')
EXCLUDED_DIRS = {'notes', 'outputs', 'audits', 'private', 'evidence', 'runs'}
EXCLUDED_DOCS = {'tasks', 'plans', 'implement', 'knowledge', 'solutions'}


def git_env(isolated=False):
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    if isolated:
        env.update({'GIT_CONFIG_NOSYSTEM': '1', 'GIT_CONFIG_GLOBAL': os.devnull,
                    'GIT_AUTHOR_NAME': 'Review Snapshot', 'GIT_AUTHOR_EMAIL': 'snapshot@invalid.local',
                    'GIT_COMMITTER_NAME': 'Review Snapshot', 'GIT_COMMITTER_EMAIL': 'snapshot@invalid.local'})
    return env


def command(args, *, cwd=None, isolated=False, input_data=None):
    result = subprocess.run(args, cwd=cwd, env=git_env(isolated), stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, input=input_data, check=False)
    if result.returncode:
        raise ValueError(f"{args[0]} {args[1] if len(args) > 1 else ''} failed: "
                         f"{result.stderr.decode(errors='replace').strip()}")
    return result.stdout


def excluded(path, blind):
    parts = PurePosixPath(path).parts
    if '.git' in parts:
        return True
    if not blind:
        return False
    if '.doc' in parts or parts[0] in EXCLUDED_DIRS:
        return True
    if len(parts) >= 2 and parts[0] == 'docs' and (
            parts[1] in EXCLUDED_DOCS or any(part in EXCLUDED_DIRS for part in parts[1:])):
        return True
    if parts[-1] == '.coderabbit.yaml':
        return True
    return False


def safe_link(path, target):
    if not target or target.startswith('/'):
        return False
    pieces = list(PurePosixPath(path).parent.parts)
    for part in PurePosixPath(target).parts:
        if part == '..':
            if not pieces:
                return False
            pieces.pop()
        elif part not in ('.', ''):
            pieces.append(part)
    return True


def archive_files(source, commit, blind):
    tracked = {}
    for record in command(['git', '-C', str(source), 'ls-tree', '-r', '-z', commit]).split(b'\0'):
        if not record:
            continue
        metadata, raw_path = record.split(b'\t', 1)
        mode, kind, oid = metadata.decode().split()
        path = os.fsdecode(raw_path)
        if kind not in ('blob', 'commit') or (kind == 'commit' and mode != '160000'):
            raise ValueError(f'unsupported tracked object: {path}')
        tracked[path] = (mode, kind, oid)
    data = command(['git', '-C', str(source), 'archive', '--format=tar', commit])
    files = {}
    omissions = []
    seen = set()
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:') as archive:
        for member in archive:
            path = member.name.rstrip('/')
            parts = PurePosixPath(path).parts
            if not path or path.startswith('/') or any(p in ('..', '.', '.git') for p in parts):
                raise ValueError(f'unsafe archive path: {member.name}')
            if not member.isdir():
                if path in seen or path not in tracked:
                    raise ValueError(f'archive contains duplicate or untracked path: {path}')
                seen.add(path)
            if excluded(path, blind):
                omissions.append(path)
                continue
            if member.isdir():
                continue
            if member.issym():
                if not safe_link(path, member.linkname):
                    raise ValueError(f'escaping symlink: {path}')
                files[path] = ('symlink', member.linkname.encode(), 0o777)
            elif member.isfile():
                stream = archive.extractfile(member)
                if stream is None:
                    raise ValueError(f'unreadable archive member: {path}')
                files[path] = ('file', stream.read(), 0o755 if member.mode & 0o111 else 0o644)
            else:
                raise ValueError(f'unsupported archive member: {path}')
    if seen != {path for path, (_, kind, _) in tracked.items() if kind == 'blob'}:
        raise ValueError(f'archive omitted tracked files at {commit}')
    for path, (mode, kind, oid) in tracked.items():
        if kind == 'commit':
            if excluded(path, blind):
                omissions.append(path)
            else:
                files[path] = ('gitlink', oid.encode(), 0o160000)
    for path, (kind, content, mode) in files.items():
        if kind == 'gitlink':
            continue
        original_mode, _, oid = tracked[path]
        if kind == 'symlink' and original_mode != '120000':
            raise ValueError(f'archive mode differs from tracked tree: {path}')
        if kind == 'file' and original_mode not in ('100644', '100755'):
            raise ValueError(f'archive mode differs from tracked tree: {path}')
        digest = hashlib.sha1() if len(oid) == 40 else hashlib.sha256()
        digest.update(b'blob ' + str(len(content)).encode() + b'\0')
        digest.update(content)
        if digest.hexdigest() != oid:
            raise ValueError(f'archive content differs from tracked blob: {path}')
    return files, omissions


def validate_manifest(raw):
    if not isinstance(raw, dict) or set(raw) != {'version', 'intent', 'repositories'}:
        raise ValueError('manifest must contain exactly version, intent, repositories')
    if type(raw['version']) is not int or raw['version'] != 1:
        raise ValueError('unsupported manifest version')
    if not isinstance(raw['intent'], str) or not raw['intent'].strip():
        raise ValueError('intent must be nonempty text')
    entries = raw['repositories']
    if not isinstance(entries, list) or not entries:
        raise ValueError('repositories must be a nonempty list')
    names = set()
    resolved = []
    for item in entries:
        if not isinstance(item, dict) or set(item) != {'name', 'path', 'base', 'head', 'role'}:
            raise ValueError('each repository requires exactly name, path, base, head, role')
        name, path = item['name'], item['path']
        if not isinstance(name, str) or not NAME.fullmatch(name) or name in names:
            raise ValueError(f'invalid or duplicate repository name: {name}')
        names.add(name)
        if not isinstance(path, str) or not Path(path).is_absolute() or not Path(path).exists():
            raise ValueError(f'repository path must be absolute and exist: {path}')
        if item['role'] not in ('change', 'context'):
            raise ValueError(f'invalid role for {name}')
        commits = []
        for key in ('base', 'head'):
            ref = item[key]
            if not isinstance(ref, str) or not ref or ref.startswith('-') or '\x00' in ref:
                raise ValueError(f'invalid {key} ref for {name}')
            value = command(['git', '-C', path, 'rev-parse', '--verify', f'{ref}^{{commit}}']).decode().strip()
            if not re.fullmatch(r'[0-9a-f]{40,64}', value):
                raise ValueError(f'invalid resolved {key} commit for {name}')
            commits.append(value)
        if item['role'] == 'context' and commits[0] != commits[1]:
            raise ValueError(f'context repository {name} must have identical base and head')
        resolved.append({'name': name, 'path': str(Path(path).resolve()),
                         'base': commits[0], 'head': commits[1], 'role': item['role']})
    if not any(item['role'] == 'change' for item in resolved):
        raise ValueError('at least one change repository is required')
    return resolved


def materialize(tree, contents):
    for child in tree.iterdir():
        if child.name != '.git':
            if child.is_dir() and not child.is_symlink():
                shutil.rmtree(child)
            else:
                child.unlink()
    for path, (kind, data, mode) in contents.items():
        target = tree / path
        target.parent.mkdir(parents=True, exist_ok=True)
        if kind == 'gitlink':
            target.mkdir()
        elif kind == 'symlink':
            target.symlink_to(data.decode())
        else:
            target.write_bytes(data)
            target.chmod(mode)
    for path, (kind, _, _) in contents.items():
        if kind == 'symlink':
            try:
                target = (tree / path).resolve(strict=False)
            except (RuntimeError, OSError) as exc:
                raise ValueError(f'unresolvable symlink: {path}') from exc
            repository_root = tree / PurePosixPath(path).parts[0]
            if not target.is_relative_to(repository_root):
                raise ValueError(f'chained symlink escapes repository: {path}')


def descriptor(files):
    return {path: {'kind': kind, 'mode': mode, 'sha256': hashlib.sha256(data).hexdigest(),
                   **({'commit': data.decode()} if kind == 'gitlink' else {})}
            for path, (kind, data, mode) in sorted(files.items())}


def stage_raw(tree, contents):
    # Stage the verified bytes directly: .gitignore and clean/text filters must
    # not change a historical snapshot while constructing its synthetic index.
    with tempfile.TemporaryDirectory(prefix='review-blobs-', dir=tree.parent) as temporary:
        blobs = {}
        for kind, data, _ in contents.values():
            if kind != 'gitlink':
                key = hashlib.sha256(data).hexdigest()
                if key not in blobs:
                    path = Path(temporary) / key
                    path.write_bytes(data)
                    blobs[key] = path
        paths = [f'../{Path(temporary).name}/{key}' for key in blobs]
        hashes = command(['git', 'hash-object', '--no-filters', '-w', '--stdin-paths'],
                         cwd=tree, isolated=True,
                         input_data=('\n'.join(paths) + '\n').encode()).decode().splitlines()
        if len(hashes) != len(blobs):
            raise ValueError('Git did not store every verified blob')
        object_ids = dict(zip(blobs, hashes))
    entries = []
    for path, (kind, data, mode) in sorted(contents.items()):
        if kind == 'gitlink':
            git_mode, oid = '160000', data.decode()
        else:
            git_mode = '120000' if kind == 'symlink' else ('100755' if mode & 0o111 else '100644')
            oid = object_ids[hashlib.sha256(data).hexdigest()]
        entries.append(f'{git_mode} {oid}\t'.encode() + os.fsencode(path) + b'\0')
    command(['git', 'read-tree', '--empty'], cwd=tree, isolated=True)
    command(['git', 'update-index', '-z', '--index-info'], cwd=tree,
            isolated=True, input_data=b''.join(entries))


def prepare(manifest_path, output, blind):
    if not output.is_absolute():
        raise ValueError('output must be absolute')
    if output.exists() or output.is_symlink():
        raise ValueError('output must be a new, nonexistent directory')
    manifest = json.loads(manifest_path.read_text())
    repos = validate_manifest(manifest)
    destination = output.resolve(strict=False)
    for entry in repos:
        source = Path(entry['path'])
        if destination == source or source in destination.parents:
            raise ValueError(f'output must be outside source repository: {source}')
    snapshots = {}
    exclusions = {}
    for entry in repos:
        pair = []
        omitted = []
        for commit in (entry['base'], entry['head']):
            files, skipped = archive_files(entry['path'], commit, blind)
            pair.append(files)
            omitted.append(skipped)
        snapshots[entry['name']] = pair
        exclusions[entry['name']] = omitted
    context = ['# Review context', '', 'Intent: ' + manifest['intent'], '',
               'Review the combined base-to-head change across all change repositories.',
               'Context repositories are pinned, complete, and unchanged.',
               'Each repository is under its named directory; its AGENTS.md files retain their usual scope.',
               'This tree is an immutable source snapshot. Do not modify it.', '', 'Sources:']
    for entry in repos:
        source_label = '' if blind else f"{entry['path']} "
        context.append(f"- {entry['name']} ({entry['role']}): {source_label}"
                       f"base {entry['base']} head {entry['head']}")
    unavailable_submodules = sorted({f"{entry['name']}/{path}"
                                     for entry in repos for files in snapshots[entry['name']]
                                     for path, (kind, _, _) in files.items() if kind == 'gitlink'})
    if unavailable_submodules:
        context += ['', 'Submodule pointers are included; their contents are unavailable in this snapshot:',
                    *[f'- {path}' for path in unavailable_submodules]]
    if blind:
        context += ['', 'Benchmark review: use local source only. External references are unavailable.',
                    'Do not install dependencies, mutate source, or make network/provider calls.',
                    'Write run artifacts outside this source tree.']
    metadata = {
        'AGENTS.md': ('file', ('# Immutable review snapshot\n\nRead REVIEW_CONTEXT.md before review. '
                               'Review all named repository directories together. '
                               'Do not alter this snapshot or its Git history.\n').encode(), 0o644),
        'REVIEW_CONTEXT.md': ('file', ('\n'.join(context) + '\n').encode(), 0o644),
    }
    if blind:
        metadata['.compound-engineering/config.yaml'] = ('file',
            b'cross_model_review_mode: off\ndocs_root: review-context\n', 0o644)
    else:
        restriction = re.compile(r'^cross_model_review_mode:\s*(?:off|[\'\"]off[\'\"])\s*(?:#.*)?$', re.M)
        for pair in snapshots.values():
            for files in pair:
                config = files.get('.compound-engineering/config.yaml')
                if config and config[0] == 'file' and restriction.search(config[1].decode(errors='replace')):
                    metadata['.compound-engineering/config.yaml'] = (
                        'file', b'cross_model_review_mode: off\n', 0o644)
                    break
    combined = []
    for side in (0, 1):
        files = dict(metadata)
        for entry in repos:
            files.update({f"{entry['name']}/{path}": value
                          for path, value in snapshots[entry['name']][side].items()})
        combined.append(files)
    created = False
    try:
        output.mkdir(parents=True, exist_ok=False)
        created = True
        tree = output / 'tree'
        tree.mkdir()
        command(['git', 'init', '-q', str(tree)], isolated=True)
        command(['git', 'config', 'core.autocrlf', 'false'], cwd=tree, isolated=True)
        # Higher-precedence local attributes keep later review diffs literal too.
        (tree / '.git/info/attributes').write_text('* -text -filter -ident\n')
        commits = []
        for side, message in enumerate(('Review snapshot base', 'Review snapshot head')):
            materialize(tree, combined[side])
            stage_raw(tree, combined[side])
            command(['git', '-c', 'core.hooksPath=/dev/null', '-c', 'commit.gpgsign=false',
                     'commit', '-q', '--allow-empty', '-m', message], cwd=tree, isolated=True)
            commits.append(command(['git', 'rev-parse', 'HEAD'], cwd=tree, isolated=True).decode().strip())
        changes = sorted(path for path in set(combined[0]) | set(combined[1])
                         if combined[0].get(path) != combined[1].get(path))
        receipt = {'version': 1, 'mode': 'blind' if blind else 'normal', 'intent': manifest['intent'],
                   'repositories': repos, 'composite': {'base': commits[0], 'head': commits[1]},
                   'files': {'base': descriptor(combined[0]), 'head': descriptor(combined[1])},
                   'counts': {'base': len(combined[0]), 'head': len(combined[1]),
                              'changed': len(changes),
                              'excluded_base': sum(len(x[0]) for x in exclusions.values()),
                              'excluded_head': sum(len(x[1]) for x in exclusions.values())},
                   'changed_files': changes, 'excluded': exclusions}
        receipt['unavailable_submodules'] = unavailable_submodules
        (output / 'manifest.lock.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
        return {'tree': str(tree), 'manifest_lock': str(output / 'manifest.lock.json'),
                'base': commits[0], 'head': commits[1]}
    except Exception:
        if created:
            shutil.rmtree(output)
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--blind', action='store_true')
    args = parser.parse_args()
    try:
        print(json.dumps(prepare(args.manifest, args.output, args.blind)))
    except (ValueError, OSError, tarfile.TarError, json.JSONDecodeError) as error:
        print(f'prepare: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
