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


def calibration_check(status='pass', required=True):
    return {'id': 'calibration', 'name': 'Independent calibration', 'status': status,
            'required': required, 'reason': 'Retained claims need fresh source calibration.',
            'evidence': ['calibration.json: pinned scope, input F1 and original worker result']}


def closure_fixture():
    report, ce = fixture()
    report['version'] = 3
    report['integration_status'] = 'complete'
    report.pop('integration_skip_reason')
    report['contract_review']['required'] = True
    integration = integration_fixture(report['source_scope'])
    concern = {'id': 'OBS1', 'title': 'Accepted representation contradicts response contract',
               'severity': 'P2', 'repository': 'apex', 'path': 'src/value.py', 'line': 8,
               'trigger': 'Save an accepted empty collection',
               'consequence': 'Successful response violates the object-only schema',
               'evidence': ['src/value.py:8 accepted input, persistence and response schema'],
               'suggested_correction': 'Admit the serialized representation',
               'validation_status': 'confirmed', 'materiality': 'consequential'}
    integration['inventory_concerns'] = [concern]
    integration['boundary_checks']['rows'][0]['concern_ids'] = ['OBS1']
    report['findings'] = [{**concern, 'id': 'F1', 'origin': 'integration'}]
    report['finding_dispositions'] = [{'stage': 'inventory', 'source_id': 'OBS1', 'action': 'retained',
                                       'finding_id': 'F1', 'reason': 'Source establishes the incompatibility',
                                       'evidence': ['src/value.py:8 producer and schema']}]
    report['checks'].append(calibration_check())
    calibration = {'scope': report['source_scope'].copy(), 'status': 'complete', 'groups': [{
        'input_ids': ['inventory/OBS1'], 'severity': 'P2', 'finding_type': 'consequential',
        'validation_status': 'confirmed', 'actor': 'Authenticated owner',
        'preconditions': ['Valid accepted collection input'], 'final_effect': concern['consequence'],
        'recovery': 'Correct the schema; no stored repair needed',
        'evidence': ['src/value.py:8 producer and schema'], 'missing_evidence': []}]}
    return report, ce, integration, calibration


def analyzer_fixture():
    report, ce = fixture()
    report['version'] = 3
    claim = {**closure_fixture()[2]['inventory_concerns'][0], 'id': 'A1',
             'severity': 'P3', 'materiality': 'low_value'}
    analyzer = {'scope': report['source_scope'].copy(), 'status': 'complete', 'findings': [claim]}
    report['findings'] = [{**claim, 'id': 'F1', 'origin': 'analyzer'}]
    report['finding_dispositions'] = [{'stage': 'analyzer', 'source_id': 'A1', 'action': 'retained',
                                       'finding_id': 'F1', 'reason': 'Source confirms the limited diagnostic',
                                       'evidence': ['src/value.py:8 source check']}]
    report['checks'].append(calibration_check())
    calibration = copy.deepcopy(closure_fixture()[3])
    calibration['groups'][0].update(input_ids=['analyzer/A1'], severity='P3', finding_type='low_value')
    return report, ce, analyzer, calibration


class AnalyzerClosureTests(unittest.TestCase):
    def decision(self, report, ce, analyzer, calibration):
        return module.recommendation(report, ce, None, manifest(), calibration, analyzer)

    def test_analyzer_only_claim_requires_actual_matching_calibration(self):
        report, ce, analyzer, calibration = analyzer_fixture()
        self.assertEqual(self.decision(report, ce, analyzer, calibration)['status'], 'pass')
        for mutation in ('missing', 'unknown', 'duplicate'):
            changed = copy.deepcopy(calibration)
            if mutation == 'missing': changed['groups'] = []
            elif mutation == 'unknown': changed['groups'][0]['input_ids'] = ['analyzer/UNKNOWN']
            else: changed['groups'] *= 2
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.decision(report, ce, analyzer, changed)

    def test_rejected_analyzer_keeps_original_candidate_and_calibration_without_final_finding(self):
        report, ce, analyzer, calibration = analyzer_fixture()
        calibration['groups'][0].update(validation_status='rejected',
                                        evidence=['src/value.py:8 source disproves the diagnostic'])
        report['findings'] = []
        report['finding_dispositions'][0].update(action='rejected', reason='Source disproves the diagnostic')
        report['finding_dispositions'][0].pop('finding_id')
        originals = copy.deepcopy((analyzer, calibration))
        self.assertEqual(self.decision(report, ce, analyzer, calibration)['status'], 'pass')
        rendered = module.render_report(report, ce, None, manifest(), calibration, analyzer)
        self.assertIn('analyzer/A1 (rejected; source P3)', rendered)
        self.assertIn('No findings supplied.', rendered)
        self.assertEqual((analyzer, calibration), originals)
        with self.assertRaises(ValueError): self.decision(report, ce, analyzer, None)
        calibration['groups'] = []
        with self.assertRaises(ValueError): self.decision(report, ce, analyzer, calibration)

    def test_analyzer_and_ce_causal_merge_preserves_both_original_ids(self):
        report, ce, analyzer, calibration = analyzer_fixture()
        ce['findings'] = [{'#': 3, 'severity': 'P3', 'materiality': 'low_value'}]
        report['findings'][0]['origin'] = 'CE'
        report['finding_dispositions'].append({**report['finding_dispositions'][0],
                                               'stage': 'ce', 'source_id': '3'})
        calibration['groups'][0]['input_ids'].append('ce/3')
        self.assertEqual(self.decision(report, ce, analyzer, calibration)['status'], 'pass')
        self.assertEqual(len(report['findings']), 1)
        rendered = module.render_report(report, ce, None, manifest(), calibration, analyzer)
        self.assertIn('analyzer/A1', rendered)
        self.assertIn('ce/3', rendered)

    def test_analyzer_reclassification_is_explicit_and_source_backed(self):
        for field, value in [('severity', 'P2'), ('materiality', 'consequential'),
                             ('validation_status', 'unresolved')]:
            report, ce, analyzer, calibration = analyzer_fixture()
            report['findings'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.decision(report, ce, analyzer, calibration)
            report['finding_dispositions'][0].update(action='reclassified', reason='Source-backed calibration disagreement')
            self.decision(report, ce, analyzer, calibration)

    def test_analyzer_receipt_scope_identity_and_provenance_are_checked(self):
        for mutation in ('absent', 'scope', 'duplicate', 'unknown_disposition', 'incomplete'):
            report, ce, analyzer, calibration = analyzer_fixture()
            if mutation == 'absent': analyzer = None
            elif mutation == 'scope': analyzer['scope']['head_sha'] = SHA_C
            elif mutation == 'duplicate': analyzer['findings'] *= 2
            elif mutation == 'incomplete': analyzer['status'] = 'degraded'
            else: report['finding_dispositions'][0]['source_id'] = 'UNKNOWN'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.decision(report, ce, analyzer, calibration)

    def test_analyzer_final_cannot_bypass_original_provenance_with_empty_groups(self):
        report, ce, _, calibration = analyzer_fixture()
        report['finding_dispositions'] = []
        calibration['groups'] = []
        with self.assertRaisesRegex(ValueError, 'provenance'):
            self.decision(report, ce, None, calibration)

    def test_renderer_cli_transports_original_analyzer_candidates(self):
        report, ce, analyzer, calibration = analyzer_fixture()
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            values = {'report': report, 'ce': ce, 'analyzer': analyzer,
                      'calibration': calibration, 'manifest': manifest()}
            for name, value in values.items():
                (root / (name + '.json')).write_text(json.dumps(value))
            originals = {name: (root / (name + '.json')).read_bytes() for name in values}
            args = [sys.executable, str(SCRIPT), '--report', str(root / 'report.json'),
                    '--ce-receipt', str(root / 'ce.json'), '--calibration-receipt', str(root / 'calibration.json'),
                    '--manifest-lock', str(root / 'manifest.json'), '--output', str(root / 'preview.md')]
            missing = subprocess.run(args, capture_output=True, text=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertFalse((root / 'preview.md').exists())
            rendered = subprocess.run(args + ['--analyzer-receipt', str(root / 'analyzer.json')],
                                      capture_output=True, text=True)
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            self.assertIn('analyzer/A1', (root / 'preview.md').read_text())
            self.assertEqual(originals, {name: (root / (name + '.json')).read_bytes() for name in values})


class InventoryClosureTests(unittest.TestCase):
    def decision(self, report, ce, integration, calibration):
        return module.recommendation(report, ce, integration, manifest(), calibration)

    def test_inventory_only_concern_reaches_final_finding_and_calibration(self):
        report, ce, integration, calibration = closure_fixture()
        self.assertEqual(self.decision(report, ce, integration, calibration)['status'], 'hold')
        rendered = module.render_report(report, ce, integration, manifest(), calibration)
        self.assertIn('inventory/OBS1', rendered)
        self.assertIn('F1', rendered)
        self.assertIn('Source establishes the incompatibility', rendered)
        self.assertEqual(integration['findings'], [])

    def test_inventory_omission_no_longer_earns_false_pass(self):
        report, ce, integration, calibration = closure_fixture()
        report['findings'] = []
        report['finding_dispositions'] = []
        with self.assertRaisesRegex(ValueError, 'disposition accounting'):
            self.decision(report, ce, integration, calibration)

    def test_inventory_accounting_rejects_missing_unknown_duplicate_and_unlinked(self):
        for mutation in ('missing_row_declaration', 'unknown_reference', 'unlinked_concern',
                         'duplicate_concern', 'duplicate_reference', 'duplicate_disposition', 'unknown_disposition'):
            report, ce, integration, calibration = closure_fixture()
            row = integration['boundary_checks']['rows'][0]
            if mutation == 'missing_row_declaration': row.pop('concern_ids')
            elif mutation == 'unknown_reference': row['concern_ids'] = ['OTHER']
            elif mutation == 'unlinked_concern': row['concern_ids'] = []
            elif mutation == 'duplicate_concern': integration['inventory_concerns'] *= 2
            elif mutation == 'duplicate_reference': row['concern_ids'] *= 2
            elif mutation == 'duplicate_disposition': report['finding_dispositions'] *= 2
            else: report['finding_dispositions'][0]['source_id'] = 'OTHER'
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.decision(report, ce, integration, calibration)

    def test_concern_can_span_multiple_rows_but_has_one_disposition(self):
        report, ce, integration, calibration = closure_fixture()
        integration['boundary_checks']['rows'].append(copy.deepcopy(integration['boundary_checks']['rows'][0]))
        self.assertEqual(self.decision(report, ce, integration, calibration)['status'], 'hold')

    def test_declared_no_concern_needs_no_extra_calibration_worker(self):
        report, ce, integration, _ = closure_fixture()
        report['findings'] = []
        report['finding_dispositions'] = []
        integration['inventory_concerns'] = []
        integration['boundary_checks']['rows'][0]['concern_ids'] = []
        report['checks'][-1].update(status='not_applicable', required=False,
                                    reason='Source inventory sweep found no raw claims or final candidates')
        self.assertEqual(self.decision(report, ce, integration, None)['status'], 'pass')
        report['checks'][-1]['evidence'] = []
        with self.assertRaises(ValueError): self.decision(report, ce, integration, None)

    def test_optional_field_inventory_concerns_use_same_closure(self):
        report, ce, integration, calibration = closure_fixture()
        integration['boundary_checks']['rows'][0]['concern_ids'] = []
        integration['optional_field_matrix'] = {'rows': [{
            'field_group': 'options', 'saved_input': 'Nonempty options',
            'omitted_result': 'Preserved', 'explicit_clear_result': 'Stored collection',
            'caller_evidence': ['src/caller.py:2'], 'evidence': ['src/value.py:8'],
            'base_head_attribution': 'Existing producer, newly exposed schema', 'concern_ids': ['OBS1']}]}
        self.assertEqual(self.decision(report, ce, integration, calibration)['status'], 'hold')
        self.assertIn('Stored collection', module.render_report(report, ce, integration, manifest(), calibration))

    def test_causal_merge_preserves_each_inventory_and_raw_source(self):
        report, ce, integration, calibration = closure_fixture()
        integration['findings'] = [{'id': 'INT1', 'severity': 'P2'}]
        report['finding_dispositions'].append({**report['finding_dispositions'][0],
                                              'stage': 'integration', 'source_id': 'INT1',
                                              'reason': 'Same schema constraint and producer'})
        calibration['groups'][0]['input_ids'].append('integration/INT1')
        self.assertEqual(self.decision(report, ce, integration, calibration)['status'], 'hold')
        output = module.render_report(report, ce, integration, manifest(), calibration)
        self.assertIn('inventory/OBS1', output)
        self.assertIn('integration/INT1', output)
        report['findings'].append({**report['findings'][0], 'id': 'F2'})
        report['finding_dispositions'][1]['finding_id'] = 'F2'
        with self.assertRaisesRegex(ValueError, 'causal group'):
            self.decision(report, ce, integration, calibration)

    def test_rejection_is_source_backed_visible_and_still_calibrated(self):
        report, ce, integration, calibration = closure_fixture()
        report['findings'] = []
        item = report['finding_dispositions'][0]
        item.update(action='rejected', reason='Source schema already admits this variant')
        item.pop('finding_id')
        calibration['groups'][0]['validation_status'] = 'rejected'
        self.assertEqual(self.decision(report, ce, integration, calibration)['status'], 'pass')
        self.assertIn('Source schema already admits', module.render_report(report, ce, integration, manifest(), calibration))
        item['evidence'] = []
        with self.assertRaises(ValueError): self.decision(report, ce, integration, calibration)

    def test_unresolved_material_concern_remains_incomplete(self):
        report, ce, integration, calibration = closure_fixture()
        report['findings'][0].update(validation_status='unresolved', materiality='unresolved')
        report['finding_dispositions'][0].update(action='reclassified', reason='Caller reachability unestablished')
        calibration['groups'][0].update(validation_status='unresolved', finding_type='unresolved',
                                         missing_evidence=['The actual caller'])
        self.assertEqual(self.decision(report, ce, integration, calibration)['status'], 'incomplete')

    def test_inventory_material_downgrade_needs_explicit_evidence(self):
        report, ce, integration, calibration = closure_fixture()
        report['findings'][0].update(severity='P3', materiality='low_value')
        with self.assertRaisesRegex(ValueError, 'reclassification'):
            self.decision(report, ce, integration, calibration)
        report['finding_dispositions'][0].update(action='reclassified', reason='Only diagnostic representation differs')
        self.assertEqual(self.decision(report, ce, integration, calibration)['status'], 'pass')
        report['finding_dispositions'][0]['evidence'] = []
        with self.assertRaises(ValueError): self.decision(report, ce, integration, calibration)

    def test_calibration_requires_exact_input_closure_even_with_no_final_findings(self):
        for mutation in ('missing_receipt', 'missing_input', 'unknown_input', 'duplicate_input',
                         'failed', 'degraded', 'wrong_scope', 'missing_source_evidence', 'skip'):
            report, ce, integration, calibration = closure_fixture()
            report['findings'] = []
            report['finding_dispositions'][0].update(action='rejected', reason='Source disproves the concern')
            report['finding_dispositions'][0].pop('finding_id')
            calibration['groups'][0]['validation_status'] = 'rejected'
            if mutation == 'missing_receipt': calibration = None
            elif mutation == 'missing_input': calibration['groups'] = []
            elif mutation == 'unknown_input': calibration['groups'][0]['input_ids'] = ['inventory/OTHER']
            elif mutation == 'duplicate_input': calibration['groups'] *= 2
            elif mutation in ('failed', 'degraded'): calibration['status'] = mutation
            elif mutation == 'wrong_scope': calibration['scope']['head_sha'] = SHA_C
            elif mutation == 'missing_source_evidence': calibration['groups'][0]['evidence'] = []
            else: report['checks'][-1].update(status='not_applicable', required=False)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.decision(report, ce, integration, calibration)

    def test_final_calibration_disagreement_must_be_explicit(self):
        report, ce, integration, calibration = closure_fixture()
        calibration['groups'][0].update(severity='P3', finding_type='low_value')
        with self.assertRaisesRegex(ValueError, 'calibration disagreement'):
            self.decision(report, ce, integration, calibration)
        report['finding_dispositions'][0].update(action='reclassified',
                                                reason='Producer and published schema establish material compatibility failure')
        self.assertEqual(self.decision(report, ce, integration, calibration)['status'], 'hold')

    def test_renderer_cli_requires_original_calibration_and_preserves_raw_inputs(self):
        report, ce, integration, calibration = closure_fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, value in [('report', report), ('ce', ce), ('integration', integration),
                                ('calibration', calibration), ('manifest', manifest())]:
                (root / f'{name}.json').write_text(json.dumps(value))
            original = {p.name: p.read_bytes() for p in root.glob('*.json')}
            command = [sys.executable, str(SCRIPT), '--report', str(root / 'report.json'),
                       '--ce-receipt', str(root / 'ce.json'), '--integration-receipt', str(root / 'integration.json'),
                       '--manifest-lock', str(root / 'manifest.json'), '--output', str(root / 'review.md')]
            missing = subprocess.run(command, text=True, capture_output=True)
            self.assertNotEqual(missing.returncode, 0)
            self.assertFalse((root / 'review.md').exists())
            rendered = subprocess.run(command + ['--calibration-receipt', str(root / 'calibration.json')],
                                      text=True, capture_output=True)
            self.assertEqual(rendered.returncode, 0, rendered.stderr)
            self.assertIn('inventory/OBS1', (root / 'review.md').read_text())
            self.assertEqual(original, {p.name: p.read_bytes() for p in root.glob('*.json')})

    def test_failed_closure_can_render_only_incomplete_or_hold(self):
        report, ce, integration, calibration = closure_fixture()
        report['findings'] = []
        report['finding_dispositions'][0].update(action='rejected', reason='Source disputes concern')
        report['finding_dispositions'][0].pop('finding_id')
        report['status'] = 'degraded'
        report['coverage_limits'] = ['Required calibration unavailable']
        for status, expected in [('unavailable', 'incomplete'), ('fail', 'hold')]:
            report['checks'][-1]['status'] = status
            with self.subTest(status=status):
                self.assertEqual(self.decision(report, ce, integration, None)['status'], expected)

    def test_legacy_v2_cannot_claim_inventory_closure(self):
        report, ce = fixture()
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'incomplete')
        self.assertIn('Legacy v2', module.render_report(report, ce, manifest_lock=manifest()))

    def test_legacy_inventory_observation_cannot_earn_false_clean(self):
        report, ce, integration, _ = closure_fixture()
        report['version'] = 2
        report['findings'] = []
        report['finding_dispositions'] = []
        self.assertEqual(module.recommendation(report, ce, integration, manifest())['status'], 'incomplete')

    def test_failed_zero_claim_calibration_cannot_turn_clean(self):
        report, ce, integration, _ = closure_fixture()
        report['findings'] = []
        report['finding_dispositions'] = []
        integration['inventory_concerns'] = []
        integration['boundary_checks']['rows'][0]['concern_ids'] = []
        report['checks'][-1]['status'] = 'unavailable'
        with self.assertRaises(ValueError): self.decision(report, ce, integration, None)
        report['status'] = 'degraded'
        report['coverage_limits'] = ['Attempted calibration unavailable']
        self.assertEqual(self.decision(report, ce, integration, None)['status'], 'incomplete')

    def test_legacy_structural_read_does_not_require_new_materiality_accounting(self):
        report, ce = ReportTests().calibration_report()
        report['checks'].append(calibration_check())
        ce['findings'][0]['finding_type'] = 'verification_gap'
        module.validate_report(report, ce, manifest_lock=manifest())
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'incomplete')


class ReportTests(unittest.TestCase):
    def calibration_report(self):
        report, ce = fixture()
        report['findings'] = [{'id': 'F1', 'title': 'Limited display failure', 'severity': 'P3',
                               'repository': 'apex', 'path': 'src/value.py', 'line': 8,
                               'trigger': 'Read value', 'consequence': 'Display omits value',
                               'evidence': ['src/value.py:8'], 'suggested_correction': 'Return value',
                               'validation_status': 'confirmed', 'materiality': 'low_value', 'origin': 'CE'}]
        ce['findings'] = [{'#': 1, 'title': 'Limited display failure', 'severity': 'P3'}]
        report['finding_dispositions'] = [{'stage': 'ce', 'source_id': '1', 'action': 'retained',
                                           'finding_id': 'F1', 'reason': 'Same defect', 'evidence': []}]
        return report, ce

    def test_v2_retained_findings_require_calibration(self):
        report, ce = self.calibration_report()
        with self.assertRaisesRegex(ValueError, 'calibration'):
            module.recommendation(report, ce, manifest_lock=manifest())

    def test_v2_complete_calibration_requires_pass_and_required(self):
        for status, required in [('fail', True), ('warning', True), ('unavailable', True),
                                 ('not_applicable', True), ('pass', False)]:
            report, ce = self.calibration_report()
            report['checks'].append(calibration_check(status, required))
            with self.subTest(status=status, required=required), self.assertRaisesRegex(ValueError, 'calibration'):
                module.recommendation(report, ce, manifest_lock=manifest())

    def test_v2_pass_calibration_retains_finding_and_requires_evidence(self):
        report, ce = self.calibration_report()
        report['checks'].append(calibration_check())
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'incomplete')
        self.assertIn('Independent calibration', module.render_report(report, ce, manifest_lock=manifest()))
        report['checks'][-1]['evidence'] = []
        with self.assertRaises(ValueError):
            module.recommendation(report, ce, manifest_lock=manifest())

    def test_v2_degraded_calibration_preserves_failure_and_coverage(self):
        for status, expected in [('fail', 'hold'), ('warning', 'incomplete'), ('unavailable', 'incomplete')]:
            report, ce = self.calibration_report()
            report['status'] = 'degraded'
            report['coverage_limits'] = ['Fresh calibration did not finish source validation.']
            report['checks'].append(calibration_check(status))
            with self.subTest(status=status):
                self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], expected)
                self.assertIn('Fresh calibration did not finish', module.render_report(report, ce, manifest_lock=manifest()))

    def test_v2_complete_zero_findings_cannot_hide_failed_calibration(self):
        for status in ('fail', 'warning', 'unavailable'):
            report, ce = fixture()
            report['checks'].append(calibration_check(status))
            for operation in (module.validate_report, module.recommendation):
                with self.subTest(status=status, operation=operation.__name__), self.assertRaisesRegex(ValueError, 'calibration'):
                    operation(report, ce, manifest_lock=manifest())

    def test_v2_zero_candidates_can_declare_calibration_inapplicable(self):
        report, ce = fixture()
        report['checks'].append(calibration_check('not_applicable', False))
        report['checks'][-1]['reason'] = 'No retained candidates remain after CE/contract source validation.'
        module.validate_report(report, ce, manifest_lock=manifest())
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'incomplete')

    def test_legacy_v1_empty_findings_failed_calibration_remains_valid(self):
        for status, expected in [('fail', 'hold'), ('warning', 'incomplete'), ('unavailable', 'incomplete')]:
            report, ce = fixture()
            report['version'] = 1
            report['checks'].append(calibration_check(status))
            with self.subTest(status=status):
                module.validate_report(report, ce, manifest_lock=manifest())
                self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], expected)

    def test_v2_duplicate_calibration_rejected_and_zero_findings_can_skip(self):
        report, ce = self.calibration_report()
        report['checks'] += [calibration_check(), calibration_check()]
        with self.assertRaises(ValueError):
            module.recommendation(report, ce, manifest_lock=manifest())
        report, ce = fixture()
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'incomplete')

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
        self.assertEqual(module.recommendation(report, ce, integration, manifest())['status'], 'incomplete')
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
        self.assertEqual(module.recommendation(report, ce, integration, manifest())['status'], 'incomplete')
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
        self.assertEqual(module.recommendation(report, ce, integration, manifest())['status'], 'incomplete')
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
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'incomplete')
        report['finding_dispositions'][0]['evidence'] = []
        with self.assertRaises(ValueError):
            module.render_report(report, ce, manifest_lock=manifest())

    def test_integration_findings_cannot_be_omitted_and_dedup_keeps_both_sources(self):
        report, ce = fixture()
        report['checks'].append(calibration_check())
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
        report['checks'].append(calibration_check())
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
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'incomplete')
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
        self.assertEqual(module.recommendation(report, ce, manifest_lock=manifest())['status'], 'incomplete')

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
        report['checks'].append(calibration_check())
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
