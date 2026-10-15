"""Behavioral tests for the bounded analyzer adapter."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'skills/sociuu-cross-repo-review/scripts/analyze.py'


class AnalyzerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.repo.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.invalid')
        self.git('config', 'user.name', 'Test')
        (self.repo / 'eslint.config.js').write_text('module.exports = {}\n')
        (self.repo / 'src').mkdir()
        (self.repo / 'src/a.js').write_text('const a = 1;\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'base')
        self.base = self.git('rev-parse', 'HEAD').strip()
        (self.repo / 'src/a.js').write_text('const a = 2;\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'head')
        self.head = self.git('rev-parse', 'HEAD').strip()

    def git(self, *args):
        return subprocess.run(['git', *args], cwd=self.repo, text=True,
                              capture_output=True, check=True).stdout

    def cli(self, *extra):
        output = self.root / 'result.json'
        proc = subprocess.run([sys.executable, str(SCRIPT), '--repository', str(self.repo),
                               '--name', 'example', '--base', self.base, '--head', self.head,
                               '--tool', 'eslint', '--output', str(output), *extra],
                              capture_output=True, text=True)
        return proc, json.loads(output.read_text()) if output.exists() else None

    def fake_eslint(self, payload, exit_code=0):
        binary = self.repo / 'node_modules/.bin/eslint'
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_text('#!/usr/bin/env python3\nimport json,sys\n'
                          'if "--version" in sys.argv: print("v9-test"); sys.exit(0)\n'
                          'print(json.dumps(' + repr(payload) + '))\n'
                          f'sys.exit({exit_code})\n')
        binary.chmod(0o755)

    def test_plan_and_missing_binary_never_pass(self):
        proc, result = self.cli()
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(result['check']['status'], 'unavailable')
        self.assertIn('planned', result['check']['reason'])
        proc, result = self.cli('--run')
        self.assertEqual(result['check']['status'], 'unavailable')
        self.assertIn('binary', result['check']['reason'])

    def test_clean_pass_requires_complete_file_result(self):
        self.fake_eslint([{'filePath': str(self.repo / 'src/a.js'), 'messages': [],
                           'errorCount': 0, 'warningCount': 0}])
        result = self.cli('--run')[1]
        self.assertEqual(result['check']['status'], 'pass')
        self.assertTrue(result['check']['evidence'])
        self.assertIn('changed eligible source files only', result['provenance']['coverage'])

    def test_timeout_is_unavailable(self):
        binary = self.repo / 'node_modules/.bin/eslint'
        binary.parent.mkdir(parents=True, exist_ok=True)
        binary.write_text('#!/usr/bin/env python3\nimport time\ntime.sleep(2)\n')
        binary.chmod(0o755)
        result = self.cli('--run', '--timeout', '0.1')[1]
        self.assertEqual(result['check']['status'], 'unavailable')

    def test_warning_and_provenance_without_mutation(self):
        self.fake_eslint([{'filePath': str(self.repo / 'src/a.js'), 'messages': [
            {'severity': 1, 'line': 1, 'column': 1, 'message': 'warning', 'ruleId': 'rule'}],
            'errorCount': 0, 'warningCount': 1}])
        before = self.git('status', '--porcelain')
        proc, result = self.cli('--run')
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(result['check']['status'], 'warning')
        self.assertEqual(result['diagnostics'][0]['path'], 'src/a.js')
        self.assertEqual(result['provenance']['base'], self.base)
        self.assertEqual(result['provenance']['head'], self.head)
        self.assertEqual(result['provenance']['tool_version'], 'v9-test')
        self.assertEqual(before, self.git('status', '--porcelain'))

    def test_error_config_failure_and_path_escape(self):
        path = str(self.repo / 'src/a.js')
        self.fake_eslint([{'filePath': path, 'messages': [
            {'severity': 2, 'line': 1, 'message': 'bad', 'ruleId': 'rule'}],
            'errorCount': 1, 'warningCount': 0}], 1)
        self.assertEqual(self.cli('--run')[1]['check']['status'], 'fail')
        self.fake_eslint([], 2)
        self.assertEqual(self.cli('--run')[1]['check']['status'], 'unavailable')
        self.fake_eslint([{'filePath': '/tmp/outside.js', 'messages': [],
                           'errorCount': 0, 'warningCount': 0}])
        self.assertEqual(self.cli('--run')[1]['check']['status'], 'unavailable')

    def test_ignored_and_malformed_results_are_unavailable(self):
        self.fake_eslint([])
        self.assertEqual(self.cli('--run')[1]['check']['status'], 'unavailable')
        binary = self.repo / 'node_modules/.bin/eslint'
        binary.write_text('#!/usr/bin/env python3\nprint("not json")\n')
        binary.chmod(0o755)
        result = self.cli('--run')[1]
        self.assertEqual(result['check']['status'], 'unavailable')
        self.assertIn('not json', result['raw']['stdout'])

    def test_phpstan_file_error_and_missing_config(self):
        (self.repo / 'src/a.php').write_text('<?php echo 1;\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'php source')
        self.head = self.git('rev-parse', 'HEAD').strip()
        output = self.root / 'phpstan.json'
        def call(env=None):
            subprocess.run([sys.executable, str(SCRIPT), '--repository', str(self.repo),
                            '--name', 'example', '--base', self.base, '--head', self.head,
                            '--tool', 'phpstan', '--output', str(output), '--run'],
                           capture_output=True, check=True, env=env)
            return json.loads(output.read_text())
        self.assertEqual(call()['check']['status'], 'unavailable')
        (self.repo / 'phpstan.neon').write_text('parameters:\n  level: 1\n')
        binary = self.repo / 'vendor/bin/phpstan'
        binary.parent.mkdir(parents=True)
        payload = {'totals': {'errors': 0, 'file_errors': 1}, 'files': {
            str(self.repo / 'src/a.php'): {'errors': 1, 'messages': [
                {'line': 1, 'message': 'invalid', 'identifier': 'test'}]}}, 'errors': []}
        binary.write_text('#!/usr/bin/env python3\nimport sys\n'
                          'if "--version" in sys.argv: print("2-test"); sys.exit(0)\n'
                          'print(' + repr(json.dumps(payload)) + ')\nsys.exit(1)\n')
        binary.chmod(0o755)
        stub = self.root / 'bin/php'
        stub.parent.mkdir()
        stub.write_text('#!/bin/sh\nexit 0\n')
        stub.chmod(0o755)
        env = dict(os.environ, PATH=str(stub.parent) + os.pathsep + os.environ['PATH'])
        result = call(env)
        self.assertEqual(result['check']['status'], 'fail')
        self.assertEqual(result['diagnostics'][0]['path'], 'src/a.php')

    def test_dirty_or_wrong_head_unavailable(self):
        self.fake_eslint([])
        (self.repo / 'src/a.js').write_text('dirty\n')
        self.assertEqual(self.cli('--run')[1]['check']['status'], 'unavailable')
        self.git('restore', 'src/a.js')
        proc, result = self.cli('--run', '--head', self.base)
        self.assertEqual(result['check']['status'], 'unavailable')

    def test_no_changed_eligible_files(self):
        (self.repo / 'src/a.js').write_text('const a = 1;\n')
        self.git('add', '.')
        self.git('commit', '-qm', 'docs')
        self.head = self.git('rev-parse', 'HEAD').strip()
        proc, result = self.cli('--run')
        self.assertEqual(result['check']['status'], 'not_applicable')


if __name__ == '__main__':
    unittest.main()
