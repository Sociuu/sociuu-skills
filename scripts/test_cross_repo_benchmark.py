"""Behavior checks for the blind-review freeze boundary."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'skills/sociuu-cross-repo-review/scripts/benchmark.py'


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.tree = self.root / 'source'
        self.tree.mkdir()
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@invalid.local')
        self.git('config', 'user.name', 'Test')
        (self.tree / 'api.php').write_text('before\n')
        self.git('add', 'api.php')
        self.git('commit', '-qm', 'Baseline')
        self.base = self.git('rev-parse', 'HEAD')
        (self.tree / 'api.php').write_text('proposed\n')
        self.git('commit', '-qam', 'Proposed')
        self.head = self.git('rev-parse', 'HEAD')
        self.candidate = self.root / 'candidate'
        self.candidate.mkdir()
        (self.candidate / 'SKILL.md').write_text('Frozen instructions\n')
        self.cases = self.root / 'cases.json'
        self.cases.write_text(json.dumps([
            {'id': name, 'tree': str(self.tree), 'base': self.base, 'head': self.head}
            for name in ('case-01', 'case-02')]))
        self.run = self.root / 'run'
        self.report = self.root / 'report.json'
        self.report.write_text(json.dumps({'status': 'complete', 'findings': [],
                                          'integration_status': 'not_applicable',
                                          'integration_skip_reason': 'No cross-repository contract changes.'}))
        self.ce = self.root / 'ce.json'
        self.ce.write_text(json.dumps({'status': 'complete', 'findings': [],
                                      'scope': {'base': self.base, 'head_sha': self.head},
                                      'reviewers': ['correctness'], 'coverage': {'depth': 'lite'}}))
        self.gold = self.root / 'gold.json'
        self.gold.write_text(json.dumps({'cases': [{'case_id': 'case-01', 'reference_findings': []}]}))

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.tree), '-c',
                                        'core.hooksPath=/dev/null', '-c',
                                        'commit.gpgsign=false', *args], text=True).strip()

    def cli(self, command, *args):
        if command == 'register':
            args = (*args, '--reference-sha256', hashlib.sha256(self.gold.read_bytes()).hexdigest())
        return subprocess.run([sys.executable, str(SCRIPT), command,
                               '--directory', str(self.run), *map(str, args)],
                              capture_output=True, text=True)

    def register(self):
        result = self.cli('register', '--candidate', self.candidate, '--cases', self.cases)
        self.assertEqual(result.returncode, 0, result.stderr)

    def freeze(self, case='case-01'):
        return self.cli('freeze', '--case', case, '--report', self.report, '--receipt', f'ce={self.ce}')

    def test_seals_outputs_before_releasing_reference(self):
        self.register()
        result = self.cli('unseal', '--expected', self.gold)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.run / 'reference.json').exists())
        self.assertEqual(self.freeze().returncode, 0)
        self.assertNotEqual(self.cli('unseal', '--expected', self.gold).returncode, 0)
        self.assertEqual(self.freeze('case-02').returncode, 0)
        result = self.cli('unseal', '--expected', self.gold)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((self.run / 'reference.json').read_bytes(), self.gold.read_bytes())
        self.assertEqual(self.cli('verify').returncode, 0)

    def test_original_output_changes_do_not_change_frozen_copy(self):
        self.register()
        self.assertEqual(self.freeze().returncode, 0)
        self.report.write_text('{"status":"complete","findings":[{"title":"later hint"}]}')
        receipts = json.loads((self.run / 'frozen/case-01.receipt.json').read_text())
        frozen = self.run / 'frozen/case-01.json'
        self.assertEqual(json.loads(frozen.read_text())['findings'], [])
        self.assertEqual(receipts['sha256'], hashlib.sha256(frozen.read_bytes()).hexdigest())
        self.assertNotEqual(self.freeze().returncode, 0)

    def test_rejects_candidate_changes_and_new_prompt_files(self):
        self.register()
        (self.candidate / 'extra.md').write_text('New review hints\n')
        self.assertNotEqual(self.freeze().returncode, 0)
        self.assertFalse((self.run / 'frozen/case-01.json').exists())

    def test_rejects_modified_packet(self):
        self.register()
        (self.tree / 'api.php').write_text('later fix\n')
        self.assertNotEqual(self.freeze().returncode, 0)
        self.assertFalse((self.run / 'frozen/case-01.json').exists())

    def test_rejects_tampered_frozen_output_before_unseal(self):
        self.register()
        self.assertEqual(self.freeze().returncode, 0)
        self.assertEqual(self.freeze('case-02').returncode, 0)
        (self.run / 'frozen/case-01.json').write_text('{"status":"complete","findings":[1]}')
        self.assertNotEqual(self.cli('unseal', '--expected', self.gold).returncode, 0)
        self.assertFalse((self.run / 'reference.json').exists())

    def test_preserves_failed_review_and_rejects_malformed_clean_report(self):
        self.register()
        self.report.write_text('{"status":"failed","findings":[],"reason":"reviewer unavailable"}')
        self.assertEqual(self.freeze().returncode, 0)
        self.report.write_text('{"findings":[]}')
        self.assertNotEqual(self.freeze('case-02').returncode, 0)
        self.report.write_text('{"status":"degraded","findings":[],"reason":"missing consumer"}')
        self.assertEqual(self.freeze('case-02').returncode, 0)
        self.assertEqual(self.cli('unseal', '--expected', self.gold).returncode, 0)
        self.assertEqual(json.loads((self.run / 'frozen/case-01.json').read_text())['status'], 'failed')

    def test_registration_cannot_be_overwritten_or_duplicate_case_ids(self):
        self.register()
        self.assertNotEqual(self.cli('register', '--candidate', self.candidate,
                                    '--cases', self.cases).returncode, 0)
        self.run = self.root / 'other-run'
        rows = json.loads(self.cases.read_text())
        rows[1]['id'] = rows[0]['id']
        self.cases.write_text(json.dumps(rows))
        self.assertNotEqual(self.cli('register', '--candidate', self.candidate,
                                    '--cases', self.cases).returncode, 0)
        self.assertFalse(self.run.exists())

    def test_reference_cannot_change_after_registration_or_unseal(self):
        self.register()
        self.assertEqual(self.freeze().returncode, 0)
        self.assertEqual(self.freeze('case-02').returncode, 0)
        original = self.gold.read_bytes()
        self.gold.write_text('{"cases":[],"changed_after_review":true}')
        self.assertNotEqual(self.cli('unseal', '--expected', self.gold).returncode, 0)
        self.assertFalse((self.run / 'reference.json').exists())
        self.gold.write_bytes(original)
        self.assertEqual(self.cli('unseal', '--expected', self.gold).returncode, 0)
        (self.run / 'reference.json').write_text('{"changed_after_unseal":true}')
        self.assertNotEqual(self.cli('verify').returncode, 0)

    def test_candidate_executable_mode_cannot_change(self):
        self.register()
        path = self.candidate / 'SKILL.md'
        path.chmod(path.stat().st_mode | 0o111)
        self.assertNotEqual(self.freeze().returncode, 0)

    def test_symlinked_candidate_directory_cannot_hide_prompts(self):
        external = self.root / 'linked-prompts'
        external.mkdir()
        (external / 'prompt.md').write_text('Review criteria\n')
        (self.candidate / 'refs').symlink_to(external, target_is_directory=True)
        result = self.cli('register', '--candidate', self.candidate, '--cases', self.cases)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.run.exists())

    def test_complete_report_requires_matching_review_receipt(self):
        self.register()
        self.assertNotEqual(self.cli('freeze', '--case', 'case-01', '--report', self.report).returncode, 0)
        ce = json.loads(self.ce.read_text())
        ce['scope']['head_sha'] = '0' * 40
        self.ce.write_text(json.dumps(ce))
        self.assertNotEqual(self.freeze().returncode, 0)
        self.assertFalse((self.run / 'frozen/case-01.json').exists())

    def test_frozen_review_receipt_cannot_change(self):
        self.register()
        self.assertEqual(self.freeze().returncode, 0)
        self.assertEqual(self.freeze('case-02').returncode, 0)
        (self.run / 'frozen/case-01.ce.json').write_text('{"status":"complete","findings":[1]}')
        self.assertNotEqual(self.cli('unseal', '--expected', self.gold).returncode, 0)
        self.assertFalse((self.run / 'reference.json').exists())

    def test_rejects_unreachable_future_git_history(self):
        self.git('commit', '--allow-empty', '-qm', 'Future correction hints')
        self.git('update-ref', 'HEAD', self.head)
        result = self.cli('register', '--candidate', self.candidate, '--cases', self.cases)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.run.exists())


if __name__ == '__main__':
    unittest.main()
