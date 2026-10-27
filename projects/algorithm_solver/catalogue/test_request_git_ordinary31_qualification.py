"""Source-free ordinary31 contract/failure controls; never executes candidates."""
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import request_git_ordinary31_qualification as owner


class PopulationAndIdentityTests(unittest.TestCase):
    def test_unselected_bool_and_bad_languages_fail_before_any_gate_or_read(self):
        for pid, lang in ((True, 'python'), (2110, 'python'), (2221, 'javascript'), (2355, 'javascript'), (1943, 'ruby')):
            with self.subTest(pid=pid, language=lang), patch.object(owner, 'authorize_before_open') as gate, patch.object(q, 'read') as read:
                with self.assertRaises(ValueError): owner.source_bytes('/unused', pid, lang, {})
                gate.assert_not_called(); read.assert_not_called()

    def test_validator_rejects_outside_population_before_oracle_dispatch(self):
        for pid in (True, 2110, 2221, 2355, '1943'):
            with self.subTest(pid=pid), self.assertRaises(ValueError): owner.validate(pid, [])

    def test_all_five_oracle_routes_are_fixed_and_validate_domains(self):
        for pid in owner.IDS:
            oracle = owner.oracle_for(pid)
            with self.subTest(pid=pid), patch.object(oracle, 'validate') as validate:
                owner.validate(pid, ['inert control'])
                validate.assert_called_once_with(pid, ['inert control'])
        for pid in owner.IDS:
            with self.subTest(pid=pid), self.assertRaises((ValueError, TypeError)):
                owner.validate(pid, [True])

    def test_additional_code_drift_fails_closed(self):
        pins = owner.additional_code()
        self.assertEqual(len(pins), 6)
        with patch.object(q, 'file_hash', return_value='0' * 64):
            with self.assertRaisesRegex(ValueError, 'immutable ordinary31 oracle'):
                owner.additional_code()

    def test_source_gate_denial_prevents_read(self):
        with patch.object(owner, 'authorize_before_open', side_effect=PermissionError('denied')), patch.object(q, 'read') as read:
            with self.assertRaises(PermissionError):
                owner.source_bytes('/unused', 1943, 'python', {'artifact_paths': {}, 'trusted_hashes': {}})
            read.assert_not_called()

    def test_exact_source_is_not_rewritten_and_both_digests_required(self):
        raw = b'inert synthetic bytes'
        spec = {**owner.BINDINGS[1943], 'source_sha256': {'python': q.sha(raw)},
                'git_blob_oid': {'python': hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()}}
        with patch.object(owner, 'binding', return_value=spec), patch.object(owner, 'authorize_before_open') as gate, patch.object(q, 'read', return_value=raw):
            self.assertEqual(owner.source_bytes('/unused', 1943, 'python', {'artifact_paths': {}, 'trusted_hashes': {}}), raw)
            gate.assert_called_once()
            spec['git_blob_oid']['python'] = '0' * 40
            with self.assertRaisesRegex(ValueError, 'Git source binding'):
                owner.source_bytes('/unused', 1943, 'python', {'artifact_paths': {}, 'trusted_hashes': {}})

    def test_runner_rejects_unselected_job_before_payloads(self):
        for pid in (2110, 2221, 2355):
            with self.subTest(pid=pid), patch.object(q, 'read') as read, patch.object(q, 'authorize_before_open') as gate:
                with self.assertRaises(ValueError):
                    q.job_inputs(Path('/unused'), {'id': pid, 'language': 'python', 'domain_validator': owner.DOMAIN}, {})
                read.assert_not_called(); gate.assert_not_called()

    def test_runner_dispatches_each_case_to_fixed_domain(self):
        cases = [{'args': [[1]], 'expected': 1}, {'args': [[2]], 'expected': 2}]
        source = b'inert bytes'; raw = q.encoded(cases)
        job = owner.make_job(Path('/unused'), 1943, 'python', cases, '/original/1943.py')
        job.update(source_sha256=q.sha(source), tests_raw_sha256=q.sha(raw), case_count=2)
        with patch.object(q, 'authorize_before_open'), patch.object(q, 'read', side_effect=[source, raw]), patch.object(owner, 'validate') as validate:
            self.assertEqual(q.job_inputs(Path('/unused'), job, {'artifact_paths': {}, 'trusted_hashes': {}}), (source, cases))
        self.assertEqual([call.args for call in validate.call_args_list], [(1943, [[1]]), (1943, [[2]])])


class ReviewAndFreezeTests(unittest.TestCase):
    def test_both_source_reviews_must_cover_exact_hash_and_oid_population(self):
        def fixture(path, pin):
            name = path.name
            if '-first-review' not in name and '-second-review' not in name: return b'{}'
            group = int(name[6]); rows = [{'problem_id': pid, 'language': lang,
                'source_sha256': owner.BINDINGS[pid]['source_sha256'][lang],
                'git_blob_oid': owner.BINDINGS[pid]['git_blob_oid'][lang]}
                for pid in owner.SOURCE_GROUPS[group] for lang in owner.LANGUAGES]
            return q.encoded({'records' if group in (1, 3) else 'rows': rows})
        with patch.object(owner, 'pinned', side_effect=fixture): owner.evidence(Path('/unused'))
        for kind in ('missing', 'duplicate', 'changed'):
            def bad(path, pin):
                raw = fixture(path, pin)
                if path.name == 'batch02-second-review.json':
                    value = q.decode(raw)
                    if kind == 'missing': value['rows'].pop()
                    elif kind == 'duplicate': value['rows'].append(value['rows'][0])
                    else: value['rows'][0]['source_sha256'] = '0' * 64
                    return q.encoded(value)
                return raw
            with self.subTest(kind=kind), patch.object(owner, 'pinned', side_effect=bad):
                with self.assertRaisesRegex(ValueError, 'two retained source reviews'):
                    owner.evidence(Path('/unused'))

    def test_selected_order_is_not_generic_order_or_retroactive_source_blindness(self):
        contract = owner.interface_contract()
        order = contract['selected_1943_order']
        self.assertTrue(order['no_normalizer'])
        self.assertFalse(order['generic_any_order_comparator_qualified'])
        self.assertIn('Any outer row order', order['public_statement_unchanged'])
        self.assertIn('post-source', contract['declaration_timing'])
        self.assertEqual(order['source_sha256'], owner.BINDINGS[1943]['source_sha256'])

    def test_approval_requires_new_population_order_and_loader_bindings(self):
        raw = q.encoded(owner.interface_contract())
        review = {'schema': 'gamma.git-ordinary31-interface-review.v1', 'independent_review': True,
            'approved': True, 'reviewer': 'independent synthetic reviewer', 'contract_sha256': q.sha(raw),
            'original_candidate_bytes_unchanged': True, 'effects_and_domain_unchanged': True,
            'original_pre_source_gaps_preserved': True, 'selected_1943_post_source_order_approved': True,
            'old_object_loader_sha256': owner.OLD_LOADER_SHA256, 'new_function_loader_sha256': owner.FUNCTION_LOADER_SHA256}
        for key, value in [('schema', 'gamma.git-subset01-interface-review.v1'), ('approved', False),
                           ('selected_1943_post_source_order_approved', False), ('contract_sha256', '0' * 64),
                           ('original_pre_source_gaps_preserved', False), ('new_function_loader_sha256', '0' * 64)]:
            with self.subTest(key=key), patch.object(owner, 'pinned', side_effect=[raw, q.encoded({**review, key: value})]):
                with self.assertRaises(ValueError): owner.approved_interface(Path('/unused'), 'external-pin')
        with patch.object(owner, 'pinned', side_effect=[raw, q.encoded(review)]):
            self.assertEqual(owner.approved_interface(Path('/unused'), 'external-pin'), (raw, q.encoded(review)))

    def test_changed_population_fails_before_evidence_or_statement_reads(self):
        with patch.object(owner, 'evidence') as evidence, patch.object(owner, 'authorize_before_open') as gate:
            for jobs in ([], [{'id': 1943, 'language': 'python'}], [{'id': 2110, 'language': 'javascript'}]):
                with self.assertRaises(ValueError): owner.verify_freeze(Path('/unused'), {'jobs': jobs}, {})
            evidence.assert_not_called(); gate.assert_not_called()

    def test_runtime_failure_precedes_metadata_payloads_and_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            args = SimpleNamespace(output=Path(tmp) / 'out')
            with patch.object(q, 'runtime', side_effect=ValueError('runtime unavailable')), patch.object(owner.KnownSpecService, 'from_config') as service:
                with self.assertRaisesRegex(ValueError, 'runtime unavailable'): owner.prepare(args)
                service.assert_not_called()
            self.assertFalse(args.output.exists())

    def test_prospective_adoption_base_cannot_replace_execution_authority(self):
        with self.assertRaisesRegex(ValueError, 'original943'):
            owner.original_base({'catalogue': {'sha256': 'prospective993'}, 'verified_receipts': {'sha256': 'new-receipts'}})

    def test_jobs_keep_exact_no_normalization_or_mutation_relaxation(self):
        for pid in owner.IDS:
            for language in owner.LANGUAGES:
                job = owner.make_job(Path('/unused'), pid, language, [], '/original/source')
                self.assertEqual(job['comparison_policy'], 'exact')
                self.assertEqual(job['source_interface'], 'commonjs-function-solve-v1' if language == 'javascript' else 'global-solve-v1')
                self.assertEqual(job['case_count'], owner.BINDINGS[pid]['case_count'])
                self.assertNotIn('node_identity', job)


class FrozenBatchTests(unittest.TestCase):
    def test_all_original_batch_schemas_preserve_offsets_counts_packets_and_projections(self):
        cases = [{'args': [3], 'expected': 7}]; cats = ['synthetic']; statement = b'inert statement'
        packet = q.encoded(q.packet(cases))
        outputs = {lang: sum(len(q.encoded({'i': i, 'result': c['expected'], 'result_type': q.expected_type(c['expected'], lang),
            'args_before': c['args'], 'args_after': c['args'], 'alias_edges': []})) for i, c in enumerate(cases)) + len(q.encoded({'done': 1})) + (lang == 'python') for lang in owner.LANGUAGES}
        for group in ('queue01', 'queue01-subset02', 'queue02-subset02', 'queue03', 'queue04'):
            want = {'offset': 0, 'count': 1, 'packet_bytes': len(packet)}
            if group in ('queue01', 'queue01-subset02'): want.update(packet_sha256=q.sha(packet), expected_observation_bytes=outputs)
            elif group == 'queue03': want['projected_output_bytes'] = max(outputs.values())
            elif group == 'queue04': want = {'offset': 0, 'calls': 1, 'packet_bytes': len(packet), 'packet_sha256': q.sha(packet), 'javascript_expected_output_bytes': outputs['javascript'], 'python_expected_output_bytes': outputs['python']}
            spec = {'oracle_group': group, 'statement_sha256': q.sha(statement), 'case_count': 1,
                'cases_sha256': q.sha(q.encoded(cases)), 'categories_sha256': q.sha(q.encoded(cats)),
                'batch_count': 1, 'batches_sha256': q.sha(q.encoded([want]))}
            oracle = SimpleNamespace(build_cases=lambda *args: (cases, cats), expected_observation_bytes=lambda batch, lang: outputs[lang])
            with self.subTest(group=group), patch.object(owner, 'binding', return_value=spec), patch.object(owner, 'oracle_for', return_value=oracle), patch.object(owner, 'validate'), patch.object(owner, 'frozen_row', return_value={'batches': [want]}):
                self.assertEqual(owner.generated(1943, statement, {}), (cases, cats))
                spec['batch_count'] = 2
                with self.assertRaisesRegex(ValueError, 'frozen batching'): owner.generated(1943, statement, {})

    def test_statement_drift_precedes_oracle_generation(self):
        oracle = SimpleNamespace(build_cases=lambda *args: self.fail('oracle must not run'))
        with patch.object(owner, 'oracle_for', return_value=oracle):
            with self.assertRaisesRegex(ValueError, 'statement bytes'): owner.generated(1943, b'drift', {})


if __name__ == '__main__': unittest.main()
