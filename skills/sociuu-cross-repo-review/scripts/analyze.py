#!/usr/bin/env python3
"""Bounded advisory analyzer for a trusted current task checkout.

CLI: --repository PATH --name NAME --base FULLSHA --head FULLSHA
     --tool eslint|phpstan --output FILE [--run] [--timeout SECONDS].
Without --run the result is an unavailable inventory plan. --run explicitly
acknowledges that the repository's installed analyzer and config may execute code.
The output is a private JSON artifact with a dossier-compatible ``check``,
source-level unresolved ``diagnostics``, ``provenance``, and separate raw streams.
Changed-file checks are limited coverage, not full-repository lint/type checks.
"""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import tempfile
import time


SHA = re.compile(r'(?:[0-9a-f]{40}|[0-9a-f]{64})\Z')
NAME = re.compile(r'[A-Za-z0-9][A-Za-z0-9_-]*\Z')
JS_SUFFIXES = ('.js', '.jsx', '.mjs', '.cjs', '.ts', '.tsx', '.mts', '.cts')
ESLINT_CONFIGS = ('eslint.config.js', 'eslint.config.mjs', 'eslint.config.cjs',
                  'eslint.config.ts', 'eslint.config.mts', 'eslint.config.cts',
                  '.eslintrc', '.eslintrc.js', '.eslintrc.cjs', '.eslintrc.json',
                  '.eslintrc.yaml', '.eslintrc.yml')
PHPSTAN_CONFIGS = ('phpstan.neon', 'phpstan.neon.dist', 'phpstan.dist.neon')
MAX_STREAM = 2_000_000


def _read_stream(stream):
    stream.seek(0)
    preview = stream.read(MAX_STREAM + 1)
    stream.seek(0)
    digest = hashlib.sha256()
    for chunk in iter(lambda: stream.read(65536), b''):
        digest.update(chunk)
    return preview, digest.hexdigest()


def _capture(command, repo, timeout):
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        try:
            proc = subprocess.run(command, cwd=repo, stdout=stdout, stderr=stderr,
                                  timeout=timeout, check=False)
        except subprocess.TimeoutExpired as exc:
            exc.stdout, _ = _read_stream(stdout)
            exc.stderr, _ = _read_stream(stderr)
            raise
        proc.stdout, stdout_hash = _read_stream(stdout)
        proc.stderr, stderr_hash = _read_stream(stderr)
        return proc, stdout_hash, stderr_hash


def _git(repo, *args):
    env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
    proc = subprocess.run(['git', '-C', str(repo), *args], stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, env=env, check=False, timeout=15)
    if proc.returncode:
        raise ValueError('git preflight failed: ' + proc.stderr.decode(errors='replace').strip())
    return proc.stdout


def _safe_path(raw, repo):
    if not isinstance(raw, str) or not raw or '\x00' in raw or '\\' in raw:
        raise ValueError('invalid analyzer path')
    path = Path(raw)
    if path.is_absolute():
        try:
            relative = path.relative_to(repo)
        except ValueError as exc:
            raise ValueError('analyzer path escapes checkout') from exc
    else:
        relative = path
    parts = PurePosixPath(relative.as_posix()).parts
    if not parts or any(p in ('', '.', '..') for p in parts):
        raise ValueError('analyzer path traverses checkout')
    candidate = repo.joinpath(*parts)
    if not candidate.resolve().is_relative_to(repo):
        raise ValueError('analyzer path resolves outside checkout')
    return relative.as_posix()


def _preflight(repo, base, head, tool):
    if not repo.is_dir() or Path(os.fsdecode(_git(repo, 'rev-parse', '--show-toplevel')).strip()).resolve() != repo:
        raise ValueError('repository must be a Git checkout root')
    if _git(repo, 'rev-parse', 'HEAD').decode().strip() != head:
        raise ValueError('checkout HEAD differs from requested head')
    for sha in (base, head):
        if _git(repo, 'rev-parse', '--verify', f'{sha}^{{commit}}').decode().strip() != sha:
            raise ValueError('base/head must resolve to supplied commit')
    _git(repo, 'merge-base', '--is-ancestor', base, head)
    if _git(repo, 'status', '--porcelain=v1', '-z', '--untracked-files=no'):
        raise ValueError('tracked checkout is dirty')
    raw = _git(repo, 'diff', '--name-only', '--diff-filter=ACMRT', '-z', base, head, '--')
    suffixes = JS_SUFFIXES if tool == 'eslint' else ('.php',)
    files = []
    for item in raw.split(b'\0'):
        if not item:
            continue
        path = _safe_path(os.fsdecode(item), repo)
        candidate = repo / path
        if path.endswith(suffixes):
            if not candidate.is_file() or candidate.is_symlink():
                raise ValueError('eligible source is not a regular file: ' + path)
            files.append(path)
    return files


def _parse_eslint(stdout, repo, eligible, exit_code):
    data = json.loads(stdout)
    if not isinstance(data, list) or exit_code not in (0, 1):
        raise ValueError('ESLint result or exit code is invalid')
    diagnostics = []
    seen = set()
    for entry in data:
        if not isinstance(entry, dict) or not isinstance(entry.get('messages'), list):
            raise ValueError('malformed ESLint result')
        path = _safe_path(entry.get('filePath'), repo)
        if path not in eligible or path in seen:
            raise ValueError('ESLint returned unexpected file')
        seen.add(path)
        if not all(type(entry.get(k)) is int and entry[k] >= 0 for k in ('errorCount', 'warningCount')):
            raise ValueError('malformed ESLint counts')
        counts = {1: 0, 2: 0}
        for message in entry['messages']:
            if not isinstance(message, dict) or message.get('severity') not in (1, 2) or not isinstance(message.get('message'), str):
                raise ValueError('malformed ESLint message')
            severity = message['severity']
            counts[severity] += 1
            if message.get('fatal'):
                raise ValueError('ESLint fatal/configuration message')
            line = message.get('line')
            if type(line) is not int or line < 1:
                raise ValueError('ESLint diagnostic lacks source line')
            diagnostics.append({'repository_path': path, 'path': path, 'line': line,
                                'severity': 'error' if severity == 2 else 'warning',
                                'message': message['message'], 'rule': message.get('ruleId'),
                                'validation_status': 'unresolved', 'origin': 'analyzer'})
        if entry['errorCount'] != counts[2] or entry['warningCount'] != counts[1]:
            raise ValueError('ESLint counts differ from messages')
    if seen != eligible:
        raise ValueError('ESLint omitted eligible files (possibly ignored)')
    errors = any(d['severity'] == 'error' for d in diagnostics)
    warnings = any(d['severity'] == 'warning' for d in diagnostics)
    if (exit_code == 1) != errors:
        raise ValueError('ESLint exit code and diagnostics disagree')
    return diagnostics, 'fail' if errors else 'warning' if warnings else 'pass'


def _parse_phpstan(stdout, repo, eligible, exit_code):
    data = json.loads(stdout)
    if not isinstance(data, dict) or not isinstance(data.get('files'), dict) or not isinstance(data.get('errors'), list):
        raise ValueError('malformed PHPStan result')
    if data['errors']:
        raise ValueError('PHPStan global errors prevent source attribution')
    diagnostics = []
    for raw_path, entry in data['files'].items():
        path = _safe_path(raw_path, repo)
        if path not in eligible or not isinstance(entry, dict) or not isinstance(entry.get('messages'), list):
            raise ValueError('PHPStan returned unexpected file or malformed messages')
        for message in entry['messages']:
            if not isinstance(message, dict) or type(message.get('line')) is not int or message['line'] < 1 or not isinstance(message.get('message'), str):
                raise ValueError('malformed PHPStan diagnostic')
            diagnostics.append({'repository_path': path, 'path': path,
                                'line': message['line'], 'severity': 'error',
                                'message': message['message'], 'rule': message.get('identifier'),
                                'validation_status': 'unresolved', 'origin': 'analyzer'})
    totals = data.get('totals')
    if not isinstance(totals, dict) or type(totals.get('file_errors')) is not int or type(totals.get('errors')) is not int:
        raise ValueError('malformed PHPStan totals')
    if totals['errors'] or totals['file_errors'] != len(diagnostics) or exit_code not in (0, 1) or (exit_code == 1) != bool(diagnostics):
        raise ValueError('PHPStan totals or exit code disagree with diagnostics')
    return diagnostics, 'fail' if diagnostics else 'pass'


def analyze(repository, name, base, head, tool, *, run=False, timeout=30):
    """Return a private analyzer artifact; expected preflight/tool failures are unavailable."""
    if not NAME.fullmatch(name) or not SHA.fullmatch(base) or not SHA.fullmatch(head):
        raise ValueError('name and full commit SHA values are required')
    if tool not in ('eslint', 'phpstan') or not math.isfinite(timeout) or timeout <= 0 or timeout > 300:
        raise ValueError('unsupported tool or timeout outside 1..300 seconds')
    repo = Path(repository).resolve()
    check = {'id': f'analyzer-{name}-{tool}', 'name': f'{name} {tool} changed files',
             'status': 'unavailable', 'required': False, 'reason': '', 'evidence': []}
    provenance = {'repository': name, 'base': base, 'head': head, 'tool': tool,
                  'command': [], 'elapsed_seconds': None, 'exit_code': None,
                  'tool_version': None, 'stdout_sha256': None, 'stderr_sha256': None,
                  'coverage': 'changed eligible source files only; not a full repository or full type check'}
    result = {'check': check, 'diagnostics': [], 'provenance': provenance,
              'raw': {'stdout': '', 'stderr': ''}}
    try:
        eligible = _preflight(repo, base, head, tool)
        provenance['eligible_files'] = eligible
        if not run:
            check['reason'] = 'planned: --run was not supplied; no analyzer executed'
            return result
        if not eligible:
            check['status'] = 'not_applicable'
            check['reason'] = 'no changed eligible source files'
            return result
        if tool == 'eslint':
            binary = repo / 'node_modules/.bin/eslint'
            configs = ESLINT_CONFIGS
            command = [str(binary), '--format', 'json', '--', *('./' + p for p in eligible)]
        else:
            binary = repo / 'vendor/bin/phpstan'
            configs = PHPSTAN_CONFIGS
            command = [str(binary), 'analyse', '--error-format=json', '--no-progress', '--',
                       *('./' + p for p in eligible)]
            if not shutil.which('php'):
                check['reason'] = 'PHP runtime unavailable'
                return result
        if not any((repo / config).is_file() for config in configs):
            check['reason'] = f'{tool} configuration unavailable'
            return result
        if not binary.is_file() or not os.access(binary, os.X_OK):
            check['reason'] = f'{tool} installed binary unavailable'
            return result
        provenance['command'] = command
        started = time.monotonic()
        try:
            version, _, _ = _capture([str(binary), '--version'], repo, min(timeout, 10))
            if version.returncode == 0:
                provenance['tool_version'] = version.stdout.decode(errors='replace').strip()[:200]
            proc, stdout_hash, stderr_hash = _capture(command, repo, timeout)
        finally:
            provenance['elapsed_seconds'] = round(time.monotonic() - started, 3)
        provenance['exit_code'] = proc.returncode
        provenance['stdout_sha256'] = stdout_hash
        provenance['stderr_sha256'] = stderr_hash
        result['raw'] = {'stdout': proc.stdout[:MAX_STREAM].decode(errors='replace'),
                         'stderr': proc.stderr[:MAX_STREAM].decode(errors='replace')}
        if len(proc.stdout) > MAX_STREAM or len(proc.stderr) > MAX_STREAM:
            raise ValueError('analyzer output exceeds bounded capture')
        parser = _parse_eslint if tool == 'eslint' else _parse_phpstan
        diagnostics, status = parser(proc.stdout.decode(), repo, set(eligible), proc.returncode)
        result['diagnostics'] = diagnostics
        check['status'] = status
        check['reason'] = 'advisory changed-file analyzer result; diagnostics remain unresolved'
        check['evidence'] = [f'base={base} head={head}',
                             f'exit={proc.returncode} stdout_sha256={provenance["stdout_sha256"]}',
                             f'changed eligible files={len(eligible)}; limited coverage']
    except (ValueError, OSError, subprocess.TimeoutExpired, UnicodeError, json.JSONDecodeError) as exc:
        if isinstance(exc, subprocess.TimeoutExpired):
            result['raw'] = {'stdout': (exc.stdout or b'')[:MAX_STREAM].decode(errors='replace'),
                             'stderr': (exc.stderr or b'')[:MAX_STREAM].decode(errors='replace')}
        check['status'] = 'unavailable'
        check['reason'] = str(exc) or type(exc).__name__
        result['diagnostics'] = []
    finally:
        if run:
            try:
                _preflight(repo, base, head, tool)
            except (ValueError, OSError, subprocess.TimeoutExpired) as exc:
                check['status'] = 'unavailable'
                check['reason'] = 'checkout drift after analyzer: ' + str(exc)
                result['diagnostics'] = []
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repository', required=True)
    parser.add_argument('--name', required=True)
    parser.add_argument('--base', required=True)
    parser.add_argument('--head', required=True)
    parser.add_argument('--tool', choices=('eslint', 'phpstan'), required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=float, default=30)
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    repo = Path(args.repository).resolve()
    output = args.output.resolve()
    if output.is_relative_to(repo):
        parser.error('output must be outside the source checkout')
    try:
        result = analyze(repo, args.name, args.base, args.head, args.tool,
                         run=args.run, timeout=args.timeout)
    except ValueError as exc:
        parser.error(str(exc))
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__':
    main()
