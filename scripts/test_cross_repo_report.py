"""Behavior tests for the cross-repository advisory report."""
import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / 'skills/sociuu-cross-repo-review/scripts/report.py'
SPEC = importlib.util.spec_from_file_location('cross_repo_report', SCRIPT)
module = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(module)
SHA_A, SHA_B, SHA_C = 'a' * 40, 'b' * 40, 'c' * 40


def fixture():
    scope = {'base': SHA_A, 'head_sha': SHA_B}
    report = {
        'version': 2, 'status': 'complete', 'source_scope': scope,
        'repositories': [{'name': 'apex', 'base': SHA_A, 'head': SHA_B, 'role': 'change'}],
        'intent': 'Expose the new value.',
        'summary': {'problem': 'Old value shown.', 'change': 'Read the new value.', 'effect': 'New value visible.'},
        'walkthrough': [{'repository': 'apex', 'paths': ['src/value.py'], 'change': 'Read value.', 'effect': 'Shows value.'}],
        'findings': [], 'finding_dispositions': [],
        'checks': [{'id': 'docs', 'name': 'Documentation', 'status': 'pass', 'required': True,
                    'reason': 'No public API changed.', 'evidence': ['docs/api.md reviewed']}],
        'qa_runbook': {'setup': ['Use synthetic tenant.'],
                       'steps': [{'action': 'Open /values', 'expected': 'New value visible', 'evidence_to_capture': 'Screenshot'}],
                       'negative_cases': [{'action': 'Open /values without access', 'expected': '403', 'evidence_to_capture': 'Response'}],
                       'cleanup': ['Delete synthetic tenant.'], 'execution_status': 'proposed', 'results': []},
        'diagrams': [], 'diagram_notes': {'sequence': 'No interaction change.', 'dbml': 'No schema change.'},
        'coverage_limits': [], 'integration_status': 'not_applicable', 'integration_skip_reason': 'Only value presentation changes.',
        'contract_review': {'required': False, 'reason': 'The source changes value presentation without a contract boundary.',
                            'evidence': ['src/value.py:8 display-only branch']}}
    ce = {'scope': scope, 'status': 'complete', 'reviewers': ['source reviewer'],
          'coverage': {'depth': 'focused'}, 'findings': []}
    return report, ce


def manifest():
    return {'version': 1, 'composite': {'base': SHA_A, 'head': SHA_B},
            'repositories': [{'name': 'apex', 'base': SHA_A, 'head': SHA_B, 'role': 'change'}]}


def integration_fixture(scope):
    return {'scope': scope.copy(), 'status': 'complete', 'findings': [],
            'boundary_checks': {'rows': [{'input_branch': 'Request value', 'validation_transformation': 'Read value',
                                          'destination': 'Response', 'observed_result': 'New value is returned',
                                          'evidence': ['src/value.py:8 branch'],
                                          'base_head_attribution': 'base: old value; head: new value'}]},
            'credential_policy_matrix': {'rows': [],
                                         'not_applicable_reason': 'The edited value flow does not carry credentials.',
                                         'not_applicable_evidence': ['src/value.py:8 input and response']}}


class ReportTests(unittest.TestCase):
    def test_legacy_v1_preserves_known_hold_precedence(self):
        report, ce = fixture()
        report['version'] = 1
        report['checks'][0]['status'] = 'fail'
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'hold')
        report['checks'][0]['status'] = 'pass'
        report['findings'] = [{'id': 'F1', 'title': 'Wrong tenant', 'severity': 'P1', 'repository': 'apex',
                               'path': 'src/value.py', 'line': 8, 'trigger': 'Cross tenant request',
                               'consequence': 'Data leak', 'evidence': ['src/value.py:8'],
                               'suggested_correction': 'Scope the query', 'validation_status': 'confirmed',
                               'materiality': 'consequential', 'origin': 'CE'}]
        ce['findings'] = [{'#': 1, 'title': 'Wrong tenant', 'severity': 'P1'}]
        report['finding_dispositions'] = [{'stage': 'ce', 'source_id': '1', 'action': 'retained',
                                           'finding_id': 'F1', 'reason': 'Same source defect', 'evidence': []}]
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'hold')

    def test_optional_contract_review_can_be_run_or_report_failure(self):
        report, ce = fixture()
        report['integration_status'] = 'complete'
        report.pop('integration_skip_reason')
        integration = integration_fixture(report['source_scope'])
        self.assertEqual(module.recommendation(report, ce, integration, manifest())['status'], 'pass')
        report['status'] = 'degraded'
        report['integration_status'] = 'failed'
        report['coverage_limits'] = ['Optional contract reviewer could not start.']
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'incomplete')

    def test_degraded_report_validates_claimed_complete_integration_coverage(self):
        report, ce = fixture()
        report['status'] = 'degraded'
        report['coverage_limits'] = ['Independent CE follow-up unavailable.']
        report['integration_status'] = 'complete'
        report.pop('integration_skip_reason')
        integration = integration_fixture(report['source_scope'])
        self.assertIn('Request value', module.render_report(report, ce, integration, manifest()))
        for bad in ({**integration, 'boundary_checks': {'rows': [{'input_branch': 'Request value'}]}},
                    {**integration, 'credential_policy_matrix': None},
                    {**integration, 'scope': {'base': SHA_A, 'head_sha': SHA_C}}):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                module.render_report(report, ce, bad, manifest())

    def test_declared_required_single_repo_contract_cannot_skip(self):
        report, ce = fixture()
        report['contract_review'] = {'required': True, 'reason': 'Return URL credentials changed.',
                                     'evidence': ['src/value.py:8 return URL branch']}
        with self.assertRaisesRegex(ValueError, 'required contract review'):
            module.render_report(report, ce, manifest_lock=manifest())
        report['integration_status'] = 'complete'
        report.pop('integration_skip_reason')
        integration = integration_fixture(report['source_scope'])
        integration['credential_policy_matrix'] = {'rows': [{
            'representation': 'URL fragment', 'source': 'Return URL', 'transformation': 'Removed before logging',
            'destination': 'Browser callback', 'policy': 'Credentials stay out of logs',
            'observed_result': 'Fragment is absent from log input', 'evidence': ['src/value.py:8 callback'],
            'base_head_attribution': 'base: logged; head: removed'}]}
        self.assertEqual(module.recommendation(report, ce, integration, manifest())['status'], 'pass')
        rendered = module.render_report(report, ce, integration, manifest())
        self.assertIn('URL fragment', rendered)
        self.assertIn('Request value', rendered)

    def test_v2_requires_evidenced_applicability(self):
        report, ce = fixture()
        for value in (None, {'required': False, 'reason': 'Presentation only.', 'evidence': []},
                      {'required': 'false', 'reason': 'Presentation only.', 'evidence': ['src/value.py:8']}):
            bad = copy.deepcopy(report)
            if value is None:
                bad.pop('contract_review')
            else:
                bad['contract_review'] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                module.render_report(bad, ce, manifest_lock=manifest())

    def test_complete_contract_receipt_requires_coverage_or_specific_nonapplicability(self):
        report, ce = fixture()
        report['integration_status'] = 'complete'
        report.pop('integration_skip_reason')
        report['contract_review']['required'] = True
        integration = integration_fixture(report['source_scope'])
        for name in ('boundary_checks', 'credential_policy_matrix'):
            bad = copy.deepcopy(integration)
            bad.pop(name)
            with self.subTest(name=name, case='missing'), self.assertRaises(ValueError):
                module.render_report(report, ce, bad, manifest())
            bad = copy.deepcopy(integration)
            bad[name] = {'rows': []}
            with self.subTest(name=name, case='unexplained-empty'), self.assertRaises(ValueError):
                module.render_report(report, ce, bad, manifest())
            bad = copy.deepcopy(integration)
            bad[name] = {'rows': [{'evidence': ['src/value.py:8']}]}
            with self.subTest(name=name, case='malformed-row'), self.assertRaises(ValueError):
                module.render_report(report, ce, bad, manifest())
        integration['boundary_checks'] = {'rows': [], 'not_applicable_reason': 'No edited entry point receives an input.',
                                          'not_applicable_evidence': ['src/value.py:8 constant source']}
        self.assertEqual(module.recommendation(report, ce, integration, manifest())['status'], 'pass')
        self.assertIn('No edited entry point', module.render_report(report, ce, integration, manifest()))

    def test_legacy_v1_renders_incomplete_for_old_false_clean_shapes(self):
        report, ce = fixture()
        report['version'] = 1
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'incomplete')
        report['integration_status'] = 'complete'
        report.pop('integration_skip_reason')
        integration = {'scope': report['source_scope'], 'status': 'complete', 'findings': []}
        self.assertEqual(module.recommendation(report, ce, integration, manifest())['status'], 'incomplete')
        self.assertIn('Legacy v1', module.render_report(report, ce, integration, manifest()))

    def test_two_changes_cannot_skip_independent_contract_review(self):
        report, ce = fixture()
        report['repositories'].append({'name': 'prime', 'base': SHA_A, 'head': SHA_B, 'role': 'change'})
        lock = manifest(); lock['repositories'].append(report['repositories'][-1].copy())
        with self.assertRaises(ValueError):
            module.render_report(report, ce, manifest_lock=lock)

    def test_receipt_finding_cannot_disappear_from_passing_report(self):
        report, ce = fixture()
        ce['findings'] = [{'#': 1, 'title': 'Wrong tenant', 'severity': 'P1'}]
        with self.assertRaises(ValueError):
            module.render_report(report, ce, manifest_lock=manifest())

    def test_old_review_cannot_be_relabelled_as_new_repository_head(self):
        report, ce = fixture()
        report['repositories'][0]['head'] = SHA_C
        with self.assertRaises(ValueError):
            module.render_report(report, ce, manifest_lock=manifest())

    def test_required_inapplicable_check_cannot_pass(self):
        report, ce = fixture()
        report['checks'][0]['status'] = 'not_applicable'
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'incomplete')

    def test_complete_report_requires_executable_qa_step(self):
        report, ce = fixture()
        report['qa_runbook']['steps'] = []
        with self.assertRaises(ValueError):
            module.render_report(report, ce, manifest_lock=manifest())

    def test_rejections_are_accounted_and_visible(self):
        report, ce = fixture()
        ce['findings'] = [{'#': 1, 'title': 'Intentional replacement', 'severity': 'P1'}]
        report['finding_dispositions'] = [{'stage': 'ce', 'source_id': '1', 'action': 'rejected',
                                           'reason': 'Replacement is the documented operation.',
                                           'evidence': ['src/value.py:8 replacement contract']}]
        output = module.render_report(report, ce, manifest_lock=manifest())
        self.assertIn('Replacement is the documented operation.', output)
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'pass')
        report['finding_dispositions'][0]['evidence'] = []
        with self.assertRaises(ValueError):
            module.render_report(report, ce, manifest_lock=manifest())

    def test_integration_findings_cannot_be_omitted_and_dedup_keeps_both_sources(self):
        report, ce = fixture()
        report['integration_status'] = 'complete'
        report['contract_review'] = {'required': True, 'reason': 'A changed input branch reaches a consumer.',
                                     'evidence': ['src/value.py:8 request branch']}
        integration = integration_fixture(report['source_scope'])
        integration['findings'] = [{'id': 'INT-1', 'title': 'Wrong value', 'severity': 'P1'}]
        with self.assertRaisesRegex(ValueError, 'disposition accounting'):
            module.render_report(report, ce, integration, manifest())
        ce['findings'] = [{'#': 1, 'title': 'Wrong value', 'severity': 'P1'}]
        report['findings'] = [{'id': 'F1', 'title': 'Wrong value', 'severity': 'P1', 'repository': 'apex',
                              'path': 'src/value.py', 'line': 8, 'trigger': 'Request the value',
                              'consequence': 'Other tenant value returned', 'evidence': ['src/value.py:8'],
                              'suggested_correction': 'Scope the query', 'validation_status': 'confirmed',
                              'materiality': 'consequential', 'origin': 'both'}]
        report['finding_dispositions'] = [
            {'stage': stage, 'source_id': source_id, 'action': 'retained', 'finding_id': 'F1',
             'reason': 'Same causal defect', 'evidence': []}
            for stage, source_id in [('ce', '1'), ('integration', 'INT-1')]]
        self.assertEqual(module.recommendation(report, ce, integration, manifest())['status'], 'hold')
        for change in ('missing', 'duplicate', 'unknown', 'missing_report_finding'):
            bad = copy.deepcopy(report)
            if change == 'missing': bad['finding_dispositions'].pop()
            elif change == 'duplicate': bad['finding_dispositions'].append(bad['finding_dispositions'][0].copy())
            elif change == 'unknown': bad['finding_dispositions'][0]['source_id'] = 'unknown'
            else: bad['finding_dispositions'][0]['finding_id'] = 'missing'
            with self.subTest(change=change), self.assertRaises(ValueError):
                module.render_report(bad, ce, integration, manifest())

    def test_snapshot_receipt_is_required_and_cannot_relabel_source(self):
        report, ce = fixture()
        with self.assertRaises(ValueError):
            module.render_report(report, ce)
        for change in ('composite', 'original', 'role', 'missing', 'duplicate'):
            lock = manifest()
            if change == 'composite': lock['composite']['head'] = SHA_C
            elif change == 'original': lock['repositories'][0]['head'] = SHA_C
            elif change == 'role': lock['repositories'][0]['role'] = 'context'
            elif change == 'missing': lock['repositories'] = []
            else: lock['repositories'].append(lock['repositories'][0].copy())
            with self.subTest(change=change), self.assertRaises(ValueError):
                module.render_report(report, ce, manifest_lock=lock)

    def test_material_receipt_finding_cannot_be_silently_downgraded(self):
        report, ce = fixture()
        ce['findings'] = [{'#': 1, 'title': 'Wrong value', 'severity': 'P1', 'validation_status': 'confirmed'}]
        report['findings'] = [{'id': 'F1', 'title': 'Intentional fallback', 'severity': 'P3', 'repository': 'apex',
                              'path': 'src/value.py', 'line': 8, 'trigger': 'Provider fails',
                              'consequence': 'Fallback is shown', 'evidence': ['src/value.py:8'],
                              'suggested_correction': 'None needed', 'validation_status': 'confirmed',
                              'materiality': 'low_value', 'origin': 'CE'}]
        report['finding_dispositions'] = [{'stage': 'ce', 'source_id': '1', 'action': 'retained',
                                          'finding_id': 'F1', 'reason': 'Same concern', 'evidence': []}]
        with self.assertRaises(ValueError):
            module.recommendation(report, ce, manifest_lock=manifest())
        report['finding_dispositions'][0].update(action='reclassified',
                                                reason='The documented fallback policy requires this behavior.',
                                                evidence=['src/value.py:8 fallback policy'])
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'pass')
        output = module.render_report(report, ce, manifest_lock=manifest())
        self.assertIn('reclassified', output)
        self.assertIn('P1', output)
        self.assertIn('fallback policy', output)
        report['finding_dispositions'][0]['evidence'] = []
        with self.assertRaises(ValueError):
            module.render_report(report, ce, manifest_lock=manifest())

    def test_failed_provider_receipt_renders_incomplete_without_fabricated_scope(self):
        report, _ = fixture()
        report['status'] = 'failed'; report['coverage_limits'] = ['CE could not start.']
        failed = {'status': 'failed', 'reason': 'Provider could not start.'}
        self.assertEqual(module.recommendation(report, failed, manifest_lock=manifest())['status'], 'incomplete')
        self.assertIn('CE could not start.', module.render_report(report, failed, manifest_lock=manifest()))

    def test_complete_report_renders_observable_sections_and_scope(self):
        report, ce = fixture()
        output = module.render_report(report, ce, manifest_lock=manifest())
        for expected in ('Summary', 'Walkthrough', 'Documentation', 'QA Runbook', 'Scope',
                         SHA_A, SHA_B, 'proposed', 'No schema change.', 'pass'):
            self.assertIn(expected, output)
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'pass')

    def test_complete_requires_matching_original_receipts(self):
        report, ce = fixture()
        ce['scope'] = {**ce['scope'], 'branch': 'review', 'pr_url': None, 'files_changed': 1}
        self.assertIn('pass', module.render_report(report, ce, manifest_lock=manifest()))
        for bad in (None, {**ce, 'scope': {'base': SHA_A, 'head_sha': SHA_C}},
                    {**ce, 'reviewers': []}, {**ce, 'coverage': {'depth': 'unknown'}}):
            with self.subTest(receipt=bad), self.assertRaises(ValueError):
                module.render_report(report, bad, manifest_lock=manifest())
        report['integration_status'] = 'complete'
        report.pop('integration_skip_reason')
        report['contract_review']['required'] = True
        with self.assertRaises(ValueError):
            module.render_report(report, ce, manifest_lock=manifest())
        integration = integration_fixture(report['source_scope'])
        self.assertIn('pass', module.render_report(report, ce, integration, manifest()))
        integration['scope'] = {'base': SHA_A, 'head_sha': SHA_C}
        with self.assertRaises(ValueError):
            module.render_report(report, ce, integration, manifest())

    def test_advisory_precedence_and_coverage(self):
        report, ce = fixture()
        report['findings'] = [{'id': 'F1', 'title': 'Wrong tenant', 'severity': 'P1', 'repository': 'apex',
                               'path': 'src/value.py', 'line': 8, 'trigger': 'Cross tenant request',
                               'consequence': 'Data leak', 'evidence': ['src/value.py:8'],
                               'suggested_correction': 'Scope the query', 'validation_status': 'confirmed',
                               'materiality': 'consequential', 'origin': 'CE'}]
        ce['findings'] = [{'#': 1, 'title': 'Wrong tenant', 'severity': 'P1'}]
        report['finding_dispositions'] = [{'stage': 'ce', 'source_id': '1', 'action': 'retained',
                                           'finding_id': 'F1', 'reason': 'Same source defect', 'evidence': []}]
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'hold')
        report['findings'][0]['validation_status'] = 'unresolved'
        report['findings'][0]['materiality'] = 'unresolved'
        report['finding_dispositions'][0].update(action='reclassified', reason='Reachability is unverified.',
                                                evidence=['src/value.py:8 caller not established'])
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'incomplete')
        report['checks'][0]['status'] = 'fail'
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'hold')
        report['checks'][0]['status'] = 'unavailable'
        report['findings'] = []
        report['finding_dispositions'] = []
        ce['findings'] = []
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'incomplete')
        report['status'] = 'degraded'
        report['finding_dispositions'] = []
        report['coverage_limits'] = ['CE did not finish.']
        self.assertEqual(module.recommendation(report, manifest_lock=manifest())['status'], 'incomplete')

    def test_rejects_invalid_evidence_and_paths(self):
        report, ce = fixture()
        variants = []
        bad = copy.deepcopy(report); bad['checks'][0]['evidence'] = []; variants.append(bad)
        bad = copy.deepcopy(report); bad['repositories'][0]['head'] = 'short'; variants.append(bad)
        bad = copy.deepcopy(report); bad['walkthrough'][0]['paths'] = ['../private']; variants.append(bad)
        bad = copy.deepcopy(report); bad['walkthrough'][0]['paths'] = ['src/./value.py']; variants.append(bad)
        bad = copy.deepcopy(report); bad['status'] = 'degraded'; variants.append(bad)
        bad = copy.deepcopy(report); bad['qa_runbook']['execution_status'] = 'verified'; variants.append(bad)
        bad = copy.deepcopy(report); bad['diagram_notes']['dbml'] = ''; variants.append(bad)
        for bad in variants:
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                module.render_report(bad, ce, manifest_lock=manifest())

    def test_source_text_is_data_including_quick_actions_and_fences(self):
        report, ce = fixture()
        report['summary']['problem'] = '<details>\n/merge\n```\nunsafe'
        report['diagrams'] = [{'kind': 'sequence', 'title': '<script>x</script>',
                               'source': 'sequenceDiagram\n```\n/approve', 'evidence': ['src/value.py:1']}]
        output = module.render_report(report, ce, manifest_lock=manifest())
        self.assertNotIn('<details>', output)
        self.assertNotIn('<script>', output)
        self.assertNotIn('\n/merge\n', output)
        self.assertNotIn('\n/approve\n', output)
        self.assertNotIn('\n```\n/approve', output)
        self.assertIn('&lt;details&gt;', output)
        self.assertIn('sequenceDiagram', output)

    def test_diagrams_preserve_executable_syntax_inside_fences(self):
        report, ce = fixture()
        source = 'sequenceDiagram\n  Client->>API: "Read value"\n  API-->>Client: Value'
        report['diagrams'] = [{'kind': 'sequence', 'title': 'Value request',
                               'source': source, 'evidence': ['src/value.py:1']}]
        self.assertIn(source, module.render_report(report, ce, manifest_lock=manifest()))

    def test_cli_writes_report_and_rejects_stale_receipt(self):
        report, ce = fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / 'report.json').write_text(json.dumps(report))
            (root / 'ce.json').write_text(json.dumps(ce))
            (root / 'manifest.json').write_text(json.dumps(manifest()))
            output = root / 'review.md'
            command = [sys.executable, str(SCRIPT), '--report', str(root / 'report.json'),
                       '--ce-receipt', str(root / 'ce.json'), '--manifest-lock', str(root / 'manifest.json'), '--output', str(output)]
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn(SHA_B, output.read_text())
            ce['scope']['head_sha'] = SHA_C
            (root / 'ce.json').write_text(json.dumps(ce))
            run = subprocess.run(command, capture_output=True, text=True)
            self.assertNotEqual(run.returncode, 0)


if __name__ == '__main__':
    unittest.main()
