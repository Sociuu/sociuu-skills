"""Public CLI tests using a fake glab executable at the process boundary."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.test_cross_repo_report import fixture, manifest, closure_fixture, analyzer_fixture, calibration_check, SHA_A, SHA_B, SHA_C


SCRIPT = Path(__file__).resolve().parents[1] / 'skills/sociuu-cross-repo-review/scripts/gitlab.py'
FAKE = '''#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
state = Path(os.environ['FAKE_STATE'])
data = json.loads(state.read_text())
args = sys.argv[1:]
data['calls'].append(args)
endpoint = args[1].split('?')[0]
method = args[args.index('--method') + 1] if '--method' in args else 'GET'
page = int(args[1].split('page=')[-1].split('&')[0]) if 'page=' in args[1] else 1
if endpoint == '/user': result = {'id': 9}
elif endpoint.endswith('/notes'):
    if method == 'GET': result = data['notes'][(page-1)*100:page*100]
    elif method == 'POST':
        body = json.loads(Path(args[args.index('--input')+1]).read_text())['body']
        item = {'id': 999, 'body': body, 'author': {'id': 9}}
        data['notes'].append(item); result = item
    else: raise Exception(args)
elif '/notes/' in endpoint:
    noteid = int(endpoint.rsplit('/', 1)[1])
    item = next(item for item in data['notes'] if item['id'] == noteid)
    if method == 'PUT': item['body'] = json.loads(Path(args[args.index('--input')+1]).read_text())['body']
    result = dict(item)
    if method == 'GET' and data.get('corrupt_readback'): result['body'] = 'different'
elif endpoint.endswith('/diffs'): result = data['diffs'][(page-1)*100:page*100]
elif '/merge_requests/' in endpoint:
    data['mr_reads'] += 1
    if 'test%2Fprime' in endpoint: result = data['prime_mr']
    else: result = data['mr_after'] if data['mr_after'] and data['mr_reads'] > data['switch_after'] else data['mr']
else: raise Exception(args)
state.write_text(json.dumps(data))
print(json.dumps(result))
'''


class GitlabTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        fake = self.root / 'glab'
        fake.write_text(FAKE)
        fake.chmod(0o755)
        self.state_path = self.root / 'state.json'
        self.state = {'calls': [], 'mr_reads': 0, 'switch_after': 1, 'mr_after': None,
                      'prime_mr': self.mr(head=SHA_C), 'corrupt_readback': False,
                      'mr': self.mr(), 'notes': [], 'diffs': [{'old_path': 'a', 'new_path': 'a'}]}
        self.save()

    def mr(self, state='opened', head=SHA_B):
        return {'iid': 7, 'state': state, 'diff_refs': {'base_sha': SHA_A, 'head_sha': head},
                'sha': head, 'web_url': 'https://gitlab.example/test/apex/-/merge_requests/7'}

    def save(self):
        self.state_path.write_text(json.dumps(self.state))

    def run_cli(self, *args):
        env = {**os.environ, 'PATH': str(self.root) + os.pathsep + os.environ['PATH'],
               'FAKE_STATE': str(self.state_path)}
        return subprocess.run([sys.executable, str(SCRIPT), *args], env=env, text=True,
                              capture_output=True)

    def loaded(self):
        return json.loads(self.state_path.read_text())

    def report_files(self):
        report, ce = fixture()
        report['version'] = 3
        report['checks'].append(calibration_check('not_applicable', False))
        report['checks'][-1]['reason'] = 'No raw or inventoried source claims or final candidates.'
        report['repositories'][0]['project'] = 'test/apex'
        for name, value in [('report', report), ('ce', ce), ('manifest', manifest())]:
            (self.root / f'{name}.json').write_text(json.dumps(value))
        return report

    def publish(self, *extra):
        self.report_files()
        return self.run_cli('publish', '--project', 'test/apex', '--mr', '7',
                            '--manifest-lock', str(self.root / 'manifest.json'), '--report', str(self.root / 'report.json'), '--ce-receipt',
                            str(self.root / 'ce.json'), '--output', str(self.root / 'preview.md'), *extra)

    def test_inspect_paginates_and_accepts_historical_states(self):
        for mr_state in ('closed', 'merged'):
            with self.subTest(state=mr_state):
                self.state['mr'] = self.mr(mr_state)
                self.state['notes'] = [{'id': i, 'body': 'note', 'author': {'id': 2}} for i in range(101)]
                self.state['diffs'] = [{'old_path': str(i)} for i in range(101)]
                self.save()
                run = self.run_cli('inspect', '--project', 'test/apex', '--mr', '7', '--output', str(self.root / 'in.json'))
                self.assertEqual(run.returncode, 0, run.stderr)
                intake = json.loads((self.root / 'in.json').read_text())
                self.assertEqual((len(intake['notes']), len(intake['diffs'])), (101, 101))
                self.assertEqual(intake['head_sha'], SHA_B)
                self.assertTrue(any('page=2' in arg for call in self.loaded()['calls'] for arg in call))

    def test_event_uses_live_refs(self):
        event = {'object_kind': 'merge_request', 'project': {'path_with_namespace': 'test/apex'},
                 'object_attributes': {'iid': 7, 'last_commit': {'id': SHA_C}}}
        (self.root / 'event.json').write_text(json.dumps(event))
        run = self.run_cli('event', '--event', str(self.root / 'event.json'), '--output', str(self.root / 'in.json'))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(json.loads((self.root / 'in.json').read_text())['head_sha'], SHA_B)

    def test_preview_has_no_mutation(self):
        run = self.publish()
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn(SHA_B, (self.root / 'preview.md').read_text())
        self.assertFalse(any('--method' in c for c in self.loaded()['calls']))

    def test_legacy_preview_is_incomplete_and_explicit_publish_rejects_before_network(self):
        report = self.report_files()
        report['version'] = 1
        (self.root / 'report.json').write_text(json.dumps(report))
        args = ('publish', '--project', 'test/apex', '--mr', '7', '--report', str(self.root / 'report.json'),
                '--ce-receipt', str(self.root / 'ce.json'), '--manifest-lock', str(self.root / 'manifest.json'),
                '--output', str(self.root / 'preview.md'))
        preview = self.run_cli(*args)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertIn('Legacy v1', (self.root / 'preview.md').read_text())
        calls_before = self.loaded()['calls']
        published = self.run_cli(*args, '--publish')
        self.assertNotEqual(published.returncode, 0)
        self.assertIn('version 3', published.stderr)
        self.assertEqual(self.loaded()['calls'], calls_before)
        self.assertEqual(self.loaded()['notes'], [])

    def test_v2_preview_is_legacy_and_cannot_publish(self):
        report = self.report_files()
        report['version'] = 2
        (self.root / 'report.json').write_text(json.dumps(report))
        args = ('publish', '--project', 'test/apex', '--mr', '7', '--report', str(self.root / 'report.json'),
                '--ce-receipt', str(self.root / 'ce.json'), '--manifest-lock', str(self.root / 'manifest.json'),
                '--output', str(self.root / 'preview.md'))
        preview = self.run_cli(*args)
        self.assertEqual(preview.returncode, 0, preview.stderr)
        self.assertIn('Legacy v2', (self.root / 'preview.md').read_text())
        calls = self.loaded()['calls']
        rejected = self.run_cli(*args, '--publish')
        self.assertNotEqual(rejected.returncode, 0)
        self.assertEqual(self.loaded()['calls'], calls)

    def test_inventory_closure_is_checked_before_publication_and_rendered(self):
        report, ce, integration, calibration = closure_fixture()
        report['repositories'][0]['project'] = 'test/apex'
        for name, value in [('report', report), ('ce', ce), ('integration', integration),
                            ('calibration', calibration), ('manifest', manifest())]:
            (self.root / f'{name}.json').write_text(json.dumps(value))
        args = ('publish', '--project', 'test/apex', '--mr', '7', '--report', str(self.root / 'report.json'),
                '--ce-receipt', str(self.root / 'ce.json'), '--integration-receipt', str(self.root / 'integration.json'),
                '--manifest-lock', str(self.root / 'manifest.json'), '--output', str(self.root / 'preview.md'), '--publish')
        missing = self.run_cli(*args)
        self.assertNotEqual(missing.returncode, 0)
        self.assertEqual(self.loaded()['calls'], [])
        published = self.run_cli(*args, '--calibration-receipt', str(self.root / 'calibration.json'))
        self.assertEqual(published.returncode, 0, published.stderr)
        body = self.loaded()['notes'][0]['body']
        self.assertIn('inventory/OBS1', body)
        self.assertIn('Final finding: F1', body)

    def test_rejected_analyzer_original_receipt_reaches_publication(self):
        report, ce, analyzer, calibration = analyzer_fixture()
        report['repositories'][0]['project'] = 'test/apex'
        report['findings'] = []
        report['finding_dispositions'][0].update(action='rejected', reason='Source disproves the diagnostic')
        report['finding_dispositions'][0].pop('finding_id')
        calibration['groups'][0]['validation_status'] = 'rejected'
        for name, value in [('report', report), ('ce', ce), ('analyzer', analyzer),
                            ('calibration', calibration), ('manifest', manifest())]:
            (self.root / f'{name}.json').write_text(json.dumps(value))
        original = (self.root / 'analyzer.json').read_bytes()
        args = ('publish', '--project', 'test/apex', '--mr', '7', '--report', str(self.root / 'report.json'),
                '--ce-receipt', str(self.root / 'ce.json'), '--calibration-receipt', str(self.root / 'calibration.json'),
                '--manifest-lock', str(self.root / 'manifest.json'), '--output', str(self.root / 'preview.md'), '--publish')
        missing = self.run_cli(*args)
        self.assertNotEqual(missing.returncode, 0)
        self.assertEqual(self.loaded()['calls'], [])
        published = self.run_cli(*args, '--analyzer-receipt', str(self.root / 'analyzer.json'))
        self.assertEqual(published.returncode, 0, published.stderr)
        body = self.loaded()['notes'][0]['body']
        self.assertIn('analyzer/A1 (rejected; source P3)', body)
        self.assertIn('No findings supplied.', body)
        self.assertEqual((self.root / 'analyzer.json').read_bytes(), original)

    def test_stale_or_closed_refuses_publication(self):
        pending_diff = self.mr()
        pending_diff['sha'] = SHA_C
        for mr in (self.mr(head=SHA_C), self.mr('closed'), pending_diff):
            with self.subTest(mr=mr):
                self.state['mr'] = mr; self.save()
                run = self.publish('--publish')
                self.assertNotEqual(run.returncode, 0)
                self.assertEqual(self.loaded()['notes'], [])

    def test_foreign_marker_and_quick_action_refuse(self):
        self.state['notes'] = [{'id': 4, 'body': '<!-- sociuu-cross-repo-review:v1 -->\n# Cross-repository review\nold', 'author': {'id': 3}}]
        self.save()
        self.assertNotEqual(self.publish('--publish').returncode, 0)
        self.state['notes'] = []; self.save()
        report = self.report_files(); report['summary']['problem'] = '/merge'
        (self.root / 'report.json').write_text(json.dumps(report))
        run = self.run_cli('publish', '--project', 'test/apex', '--mr', '7', '--report',
                           str(self.root / 'report.json'), '--ce-receipt', str(self.root / 'ce.json'),
                           '--manifest-lock', str(self.root / 'manifest.json'),
                           '--output', str(self.root / 'preview.md'), '--publish')
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertNotIn('\n/merge', self.loaded()['notes'][0]['body'])

    def test_one_note_idempotent_and_readback(self):
        self.assertEqual(self.publish('--publish').returncode, 0)
        self.assertEqual(self.publish('--publish').returncode, 0)
        state = self.loaded()
        self.assertEqual(len(state['notes']), 1)
        methods = [c[c.index('--method')+1] for c in state['calls'] if '--method' in c]
        self.assertEqual(methods, ['POST'])
        self.assertTrue(any('/notes/999' in arg for call in state['calls'] for arg in call))

    def test_same_author_human_note_quoting_marker_is_preserved(self):
        human = {'id': 4, 'body': 'Please use <!-- sociuu-cross-repo-review:v1 --> for the bot.',
                 'author': {'id': 9}}
        self.state['notes'] = [human.copy()]; self.save()
        self.assertEqual(self.publish('--publish').returncode, 0)
        notes = self.loaded()['notes']
        self.assertEqual(len(notes), 2)
        self.assertEqual(notes[0], human)

    def test_existing_managed_note_is_updated_without_replacing_human_text(self):
        self.assertEqual(self.publish('--publish').returncode, 0)
        self.state = self.loaded()
        self.state['notes'].insert(0, {'id': 4, 'body': 'Human explanation', 'author': {'id': 9}})
        human = self.state['notes'][0].copy(); self.save()
        report = self.report_files()
        report['summary']['effect'] = 'Updated explanation'
        (self.root / 'report.json').write_text(json.dumps(report))
        run = self.run_cli('publish', '--project', 'test/apex', '--mr', '7',
                           '--manifest-lock', str(self.root / 'manifest.json'),
                           '--report', str(self.root / 'report.json'), '--ce-receipt',
                           str(self.root / 'ce.json'), '--output', str(self.root / 'preview.md'), '--publish')
        self.assertEqual(run.returncode, 0, run.stderr)
        state = self.loaded()
        self.assertEqual(state['notes'][0], human)
        self.assertEqual(state['notes'][1]['id'], 999)
        self.assertIn('Updated explanation', state['notes'][1]['body'])
        self.assertEqual(len(state['notes']), 2)
        self.assertTrue(any('--method' in c and 'PUT' in c for c in state['calls']))

    def test_readback_failure_identifies_written_note(self):
        self.state['corrupt_readback'] = True; self.save()
        run = self.publish('--publish')
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('note 999', run.stderr)
        self.assertIn('reconciliation required', run.stderr)
        self.assertEqual(len(self.loaded()['notes']), 1)

    def test_race_refuses_and_companion_requires_current_refs(self):
        self.state['mr_after'] = self.mr(head=SHA_C); self.save()
        self.assertNotEqual(self.publish('--publish').returncode, 0)
        self.assertEqual(self.loaded()['notes'], [])
        self.state['mr_after'] = None; self.state['mr_reads'] = 0; self.save()
        report = self.report_files()
        report['repositories'].append({'name': 'prime', 'project': 'test/prime', 'base': SHA_A,
                                       'head': SHA_B, 'role': 'change'})
        report['status'] = 'degraded'; report['integration_status'] = 'degraded'
        report['contract_review'] = {'required': True, 'reason': 'Two repositories changed.',
                                     'evidence': ['apex and prime manifest change entries']}
        report['coverage_limits'] = ['Companion review incomplete.']
        lock = manifest(); lock['repositories'].append({k:v for k,v in report['repositories'][-1].items() if k != 'project'})
        (self.root / 'manifest.json').write_text(json.dumps(lock))
        (self.root / 'report.json').write_text(json.dumps(report))
        self.assertNotEqual(self.run_cli('publish', '--project', 'test/apex', '--mr', '7',
                            '--manifest-lock', str(self.root / 'manifest.json'), '--report', str(self.root / 'report.json'), '--ce-receipt',
                            str(self.root / 'ce.json'), '--output', str(self.root / 'preview.md'),
                            '--publish').returncode, 0)
        self.assertEqual(self.loaded()['notes'], [])
        run = self.run_cli('publish', '--project', 'test/apex', '--mr', '7',
                           '--manifest-lock', str(self.root / 'manifest.json'), '--report', str(self.root / 'report.json'), '--ce-receipt',
                           str(self.root / 'ce.json'), '--output', str(self.root / 'preview.md'),
                           '--companion', 'test/prime!8', '--publish')
        self.assertNotEqual(run.returncode, 0)
        self.assertIn('test/prime!8 source revisions changed', run.stderr)
        self.assertEqual(self.loaded()['notes'], [])


if __name__ == '__main__':
    unittest.main()
