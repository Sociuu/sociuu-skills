"""Integration checks for immutable cross-repository review snapshots."""
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


CLI = Path(__file__).resolve().parents[1] / 'skills/sociuu-cross-repo-review/scripts/prepare.py'


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True).strip()


class PrepareTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def repo(self, name, first, second):
        path = self.root / name
        path.mkdir()
        subprocess.run(['git', 'init', '-q', str(path)], check=True)
        git(path, 'config', 'user.name', 'Fixture')
        git(path, 'config', 'user.email', 'fixture@example.test')
        for filename, content in first.items():
            target = path / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
        git(path, 'add', '-A')
        git(path, 'commit', '-qm', 'first')
        base = git(path, 'rev-parse', 'HEAD')
        for filename, content in second.items():
            target = path / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            if content is None:
                target.unlink()
            else:
                target.write_text(content)
        git(path, 'add', '-A')
        git(path, 'commit', '-qm', 'second')
        head = git(path, 'rev-parse', 'HEAD')
        return path, base, head

    def prepare(self, repositories, *, blind=False, output=None):
        manifest = self.root / 'input.json'
        manifest.write_text(json.dumps({'version': 1, 'intent': 'A neutral behavior change.', 'repositories': repositories}))
        output = output or self.root / 'result'
        cmd = [sys.executable, str(CLI), str(manifest), '--output', str(output)]
        if blind:
            cmd.append('--blind')
        return subprocess.run(cmd, text=True, capture_output=True), output

    @staticmethod
    def entry(name, path, base, head, role='change'):
        return {'name': name, 'path': str(path), 'base': base, 'head': head, 'role': role}

    def test_pinned_combined_diff_ignores_dirty_and_future_source(self):
        a, a0, a1 = self.repo('a', {'src/a.txt': 'old\n'}, {'src/a.txt': 'new\n'})
        b, b0, _ = self.repo('b', {'src/b.txt': 'stable\n'}, {'src/b.txt': 'future\n'})
        (a / 'src/a.txt').write_text('dirty\n')
        before = git(a, 'status', '--porcelain')
        result, output = self.prepare([self.entry('a', a, a0, a1), self.entry('b', b, b0, b0, 'context')])
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        tree = Path(payload['tree'])
        self.assertEqual((tree / 'a/src/a.txt').read_text(), 'new\n')
        self.assertEqual((tree / 'b/src/b.txt').read_text(), 'stable\n')
        diff = git(tree, 'diff', '--name-only', payload['base'], payload['head']).splitlines()
        self.assertEqual(diff, ['a/src/a.txt'])
        self.assertEqual(git(a, 'status', '--porcelain'), before)
        self.assertEqual(len(git(tree, 'rev-list', '--all').splitlines()), 2)
        self.assertTrue((output / 'manifest.lock.json').exists())
        self.assertEqual(git(tree, 'remote'), '')

    def test_blind_excludes_answers_but_keeps_source_and_stable_rules(self):
        a, a0, a1 = self.repo('a', {'src/a.py': 'x = 1\n', 'AGENTS.md': 'Review rules\n', 'docs/tasks/answer.md': 'expected fix\n'},
                              {'src/a.py': 'x = 2\n', 'docs/tasks/answer.md': 'new answer\n'})
        result, _ = self.prepare([self.entry('a', a, a0, a1)], blind=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        tree = Path(payload['tree'])
        self.assertFalse((tree / 'a/docs/tasks').exists())
        self.assertNotIn(str(a), (tree / 'REVIEW_CONTEXT.md').read_text())
        self.assertTrue((tree / 'a/AGENTS.md').exists())
        self.assertIn('cross_model_review_mode: off', (tree / '.compound-engineering/config.yaml').read_text())
        self.assertNotIn('answer', git(tree, 'diff', '--name-only', payload['base'], payload['head']))
        self.assertEqual(git(tree, 'show', f"{payload['base']}:REVIEW_CONTEXT.md"),
                         git(tree, 'show', f"{payload['head']}:REVIEW_CONTEXT.md"))

    def test_rejects_bad_manifest_and_existing_output(self):
        a, a0, a1 = self.repo('a', {'x': 'a'}, {'x': 'b'})
        invalid = [
            [self.entry('../bad', a, a0, a1)],
            [self.entry('a', a, 'missing-ref', a1)],
            [self.entry('a', a, a0, a1, 'context')],
            [self.entry('a', a, a0, a1), self.entry('a', a, a0, a1)],
        ]
        for entries in invalid:
            with self.subTest(entries=entries):
                result, output = self.prepare(entries)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse(output.exists())
        existing = self.root / 'existing'
        existing.mkdir()
        result, _ = self.prepare([self.entry('a', a, a0, a1)], output=existing)
        self.assertNotEqual(result.returncode, 0)
        result, _ = self.prepare([self.entry('a', a, a0, a1)], output=a / 'new-output')
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((a / 'new-output').exists())

    def test_blind_preserves_product_benchmarks_labels_and_expected_fixtures(self):
        source = {'app/Benchmark/Report.php': 'old report\n',
                  'src/label.ts': 'old label\n',
                  'tests/expected.json': '{"value": 1}\n',
                  'contracts/derive_expected.py': 'expected = 1\n',
                  'docs/tasks/expected-findings.md': 'private review answers\n'}
        changes = {path: content.replace('old', 'new').replace('1', '2')
                   for path, content in source.items()}
        a, a0, a1 = self.repo('a', source, changes)
        result, _ = self.prepare([self.entry('a', a, a0, a1)], blind=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        tree = Path(payload['tree'])
        for path, content in changes.items():
            if path.startswith('docs/tasks/'):
                self.assertFalse((tree / 'a' / path).exists())
            else:
                self.assertEqual((tree / 'a' / path).read_text(), content)
                self.assertEqual(git(tree, 'show', f"{payload['base']}:a/{path}"), source[path].strip())

    def test_blind_metadata_directory_names_do_not_hide_application_source(self):
        source = {f'src/{name}/module.py': 'value = 1\n'
                  for name in ('notes', 'private', 'evidence', 'runs', 'outputs', 'audits')}
        source.update({'private/reference.json': 'hidden reference\n',
                       'docs/testing/evidence/reference.json': 'hidden evidence\n'})
        changes = {path: content.replace('1', '2') for path, content in source.items()}
        a, a0, a1 = self.repo('a', source, changes)
        result, _ = self.prepare([self.entry('a', a, a0, a1)], blind=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        tree = Path(payload['tree'])
        for path, content in changes.items():
            if path.startswith('src/'):
                self.assertEqual((tree / 'a' / path).read_text(), content)
                self.assertEqual(git(tree, 'show', f"{payload['base']}:a/{path}"), source[path].strip())
            else:
                self.assertFalse((tree / 'a' / path).exists())

    def test_rejects_escaping_symlink_without_partial_output(self):
        a, a0, _ = self.repo('a', {'safe': 'content'}, {'safe': 'new'})
        os.symlink('../../outside', a / 'escape')
        git(a, 'add', 'escape')
        git(a, 'commit', '-qm', 'link')
        a1 = git(a, 'rev-parse', 'HEAD')
        result, output = self.prepare([self.entry('a', a, a0, a1)])
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists())

    def test_rejects_archive_attributes_that_hide_tracked_source(self):
        a, a0, a1 = self.repo('a', {'src.py': 'old\n', '.gitattributes': 'src.py export-ignore\n'},
                              {'src.py': 'new\n'})
        result, output = self.prepare([self.entry('a', a, a0, a1)])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('omitted tracked files', result.stderr)
        self.assertFalse(output.exists())

    def test_rejects_archive_attributes_that_rewrite_tracked_blob(self):
        a, a0, a1 = self.repo('a', {'src.txt': '$Format:%H$\n',
                                   '.gitattributes': 'src.txt export-subst\n'},
                              {'other.txt': 'new\n'})
        result, output = self.prepare([self.entry('a', a, a0, a1)])
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('content differs', result.stderr)
        self.assertFalse(output.exists())

    def test_normal_mode_preserves_explicit_source_review_restriction(self):
        a, a0, a1 = self.repo('a', {'.compound-engineering/config.yaml': 'cross_model_review_mode: off\n',
                                   'src.txt': 'old\n'}, {'src.txt': 'new\n'})
        result, _ = self.prepare([self.entry('a', a, a0, a1)])
        self.assertEqual(result.returncode, 0, result.stderr)
        tree = Path(json.loads(result.stdout)['tree'])
        self.assertEqual((tree / '.compound-engineering/config.yaml').read_text(),
                         'cross_model_review_mode: off\n')

    def test_preserves_deletions_executable_mode_and_binary_blob(self):
        a, a0, _ = self.repo('a', {'old.txt': 'gone\n', 'run.sh': '#!/bin/sh\nexit 0\n'},
                              {'old.txt': None, 'run.sh': '#!/bin/sh\nexit 1\n'})
        script = a / 'run.sh'
        script.chmod(0o755)
        (a / 'blob.bin').write_bytes(b'\x00\xff\x01')
        git(a, 'add', '-A')
        git(a, 'commit', '-qm', 'binary and mode')
        a1 = git(a, 'rev-parse', 'HEAD')
        result, _ = self.prepare([self.entry('a', a, a0, a1)])
        self.assertEqual(result.returncode, 0, result.stderr)
        tree = Path(json.loads(result.stdout)['tree'])
        self.assertFalse((tree / 'a/old.txt').exists())
        self.assertTrue((tree / 'a/run.sh').stat().st_mode & 0o111)
        self.assertEqual((tree / 'a/blob.bin').read_bytes(), b'\x00\xff\x01')

    def test_preserves_gitlink_pointers_without_submodule_objects(self):
        a, _, _ = self.repo('a', {'src.txt': 'stable\n'}, {'src.txt': 'changed\n'})
        old_pointer = '1' * 40
        new_pointer = '2' * 40
        git(a, 'update-index', '--add', '--cacheinfo', f'160000,{old_pointer},vendor/tool')
        git(a, 'commit', '-qm', 'old pointer')
        a0 = git(a, 'rev-parse', 'HEAD')
        git(a, 'update-index', '--add', '--cacheinfo', f'160000,{new_pointer},vendor/tool')
        git(a, 'commit', '-qm', 'new pointer')
        a1 = git(a, 'rev-parse', 'HEAD')
        b, _, _ = self.repo('b', {'context.txt': 'stable\n'}, {'context.txt': 'still stable\n'})
        context_pointer = '3' * 40
        git(b, 'update-index', '--add', '--cacheinfo', f'160000,{context_pointer},vendor/context')
        git(b, 'commit', '-qm', 'context pointer')
        b0 = git(b, 'rev-parse', 'HEAD')
        before = git(a, 'status', '--porcelain')
        result, output = self.prepare([self.entry('a', a, a0, a1),
                                       self.entry('b', b, b0, b0, 'context')])
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        tree = Path(payload['tree'])
        self.assertIn(f'160000 commit {old_pointer}\ta/vendor/tool',
                      git(tree, 'ls-tree', '-r', payload['base']))
        self.assertIn(f'160000 commit {new_pointer}\ta/vendor/tool',
                      git(tree, 'ls-tree', '-r', payload['head']))
        for side in ('base', 'head'):
            self.assertIn(f'160000 commit {context_pointer}\tb/vendor/context',
                          git(tree, 'ls-tree', '-r', payload[side]))
        self.assertIn('a/vendor/tool', git(tree, 'diff', '--name-only', payload['base'], payload['head']))
        self.assertIn('submodule', (tree / 'REVIEW_CONTEXT.md').read_text().lower())
        receipt = json.loads((output / 'manifest.lock.json').read_text())
        self.assertIn('a/vendor/tool', receipt['unavailable_submodules'])
        self.assertIn('b/vendor/context', receipt['unavailable_submodules'])
        self.assertEqual(git(a, 'status', '--porcelain'), before)

    def test_preserves_tracked_ignored_source(self):
        a, a0, _ = self.repo('a', {'kept.txt': 'tracked\n'}, {'kept.txt': 'updated\n'})
        (a / '.gitignore').write_text('kept.txt\n')
        git(a, 'add', '.gitignore')
        git(a, 'commit', '-qm', 'ignore rule')
        a0 = git(a, 'rev-parse', 'HEAD')
        (a / 'kept.txt').write_text('updated again\n')
        git(a, 'add', 'kept.txt')
        git(a, 'commit', '-qm', 'tracked update')
        a1 = git(a, 'rev-parse', 'HEAD')
        result, _ = self.prepare([self.entry('a', a, a0, a1)])
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        tree = Path(payload['tree'])
        self.assertIn('a/kept.txt', git(tree, 'ls-files').splitlines())
        self.assertEqual(git(tree, 'show', f"{payload['head']}:a/kept.txt"), 'updated again')
        self.assertEqual(git(tree, 'status', '--porcelain'), '')

    def test_attribute_change_does_not_normalize_unchanged_source(self):
        a, _, _ = self.repo('a', {'x.txt': 'first\n'}, {'x.txt': 'second\n'})
        (a / 'x.txt').write_bytes(b'line\r\n')
        git(a, 'add', 'x.txt')
        git(a, 'commit', '-qm', 'raw bytes')
        a0 = git(a, 'rev-parse', 'HEAD')
        (a / '.gitattributes').write_text('*.txt text\n')
        git(a, 'add', '.gitattributes')
        git(a, 'commit', '-qm', 'attribute only')
        a1 = git(a, 'rev-parse', 'HEAD')
        result, _ = self.prepare([self.entry('a', a, a0, a1)])
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        tree = Path(payload['tree'])
        actual = subprocess.check_output(['git', '-C', str(tree), 'show', f"{payload['head']}:a/x.txt"])
        self.assertEqual(actual, b'line\r\n')
        self.assertEqual(git(tree, 'diff', '--name-only', payload['base'], payload['head']), 'a/.gitattributes')
        self.assertEqual(git(tree, 'status', '--porcelain'), '')

    def test_rejects_chained_symlink_escape(self):
        a, a0, _ = self.repo('a', {'sub/keep.txt': 'safe'}, {'sub/keep.txt': 'updated'})
        (a / 'sub/a').symlink_to('..')
        (a / 'x').symlink_to('sub/a/../../outside')
        git(a, 'add', 'sub/a', 'x')
        git(a, 'commit', '-qm', 'chained link')
        a1 = git(a, 'rev-parse', 'HEAD')
        result, output = self.prepare([self.entry('a', a, a0, a1)])
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
