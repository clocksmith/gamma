"""An exact archive with unpriced dependencies is not a counted score."""
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from projects.enwiki9.tools import hutter_upper_bound_certificate as certificate


class UnknownCostsTests(unittest.TestCase):
    def load(self, **fields):
        data = dict(program_id='unpriced', data_size=10000000, data_sha256='fixed',
                    compressed_size=1305268, roundtrip_ok=True,
                    determinism={'single_host_byte_equal': True})
        data.update(fields)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'result.json'
            path.write_text(json.dumps(data))
            row = certificate.load_result(path)
        return replace(row, path=certificate.ROOT / 'results/fixture/result.json')

    def test_absent_null_and_invalid_costs_are_unknown_not_zero(self):
        for fields in ({}, {'program_size': None, 'hutter_score': None},
                       {'program_size': False}, {'program_size': -1},
                       {'program_size': 'unknown'}, {'program_size': 1.5},
                       {'program_size': '\u00b2'}, {'program_size': '9' * 10000}):
            with self.subTest(fields=fields):
                row = self.load(**fields)
                self.assertIsNone(row.program_size)
                self.assertIsNone(row.hutter_score)
                self.assertIsNone(row.percent)
                self.assertTrue(row.is_constructive)

    def test_explicit_unknown_score_is_not_replaced_by_component_subtotal(self):
        row = self.load(program_size=200, hutter_score=None)
        self.assertEqual(row.program_size, 200)
        self.assertIsNone(row.hutter_score)

    def test_legacy_known_components_and_explicit_zero_remain_distinct(self):
        self.assertEqual(self.load(program_size=200).hutter_score, 1305468)
        row = self.load(program_size=0)
        self.assertEqual((row.program_size, row.hutter_score), (0, 1305268))

    def test_unpriced_smaller_archive_cannot_displace_counted_upper_bound(self):
        unpriced = self.load(program_size=None, hutter_score=None)
        priced = replace(unpriced, program_id='priced', compressed_size=1400000,
                         program_size=200, hutter_score=1400200)
        self.assertEqual(certificate.best_by_size([unpriced, priced]), [priced])
        self.assertEqual(certificate.best_archive_by_size([priced, unpriced]), [unpriced])
        with mock.patch.object(certificate, 'build_top_status', return_value=[]):
            result = certificate.build_certificate([unpriced, priced])
        self.assertEqual(result['proof_status']['best_constructive_ratio_any_scope']['program_id'], 'priced')
        archive, = result['best_exact_archive_by_scope']
        self.assertIsNone(archive['program_size'])
        self.assertIsNone(archive['hutter_score'])
        self.assertIsNone(archive['score_percent'])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'report.md'
            certificate.write_markdown(result, path)
            self.assertIn('1,305,268 | unknown | unknown', path.read_text())

    def test_full_corpus_unknown_score_cannot_certify_even_with_other_flags(self):
        row = replace(self.load(program_size=None, hutter_score=None),
                      data_size=certificate.FULL_INPUT_BYTES,
                      data_sha256=certificate.OBJECTIVE_BINDING['corpusSha256'],
                      objective_digest=certificate.OBJECTIVE_BINDING['objectiveDigest'],
                      score_accounting_complete=True, dependency_closure_complete=True,
                      resource_evidence_complete=True, independent_decode_ok=True,
                      license_audit_ok=True, prize_claimable=True)
        self.assertFalse(row.is_full_corpus_proof)
        with mock.patch.object(certificate, 'build_top_status', return_value=[]):
            result = certificate.build_certificate([row])
        self.assertFalse(result['proof_status']['has_full_corpus_constructive_result'])
        self.assertFalse(result['proof_status']['has_10_95_constructive_upper_bound'])
        self.assertIsNone(result['proof_status']['best_constructive_ratio_any_scope'])
        self.assertEqual(result['best_exact_upper_bounds_by_scope'], [])
        self.assertEqual(len(result['best_exact_archive_by_scope']), 1)


if __name__ == '__main__':
    unittest.main()
