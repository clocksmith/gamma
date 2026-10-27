"""Exact additive replay transitions; inert identities, no candidate payloads."""
from pathlib import Path
import unittest
from unittest.mock import patch

from . import imported_qualification as q
from . import public_batch_adapter as adapter
from . import request_cohort02_qualification as cohort

RESULT_V1 = 'b601c7d128a1a21e85d605766ad7456142852c6fbcf18c431ec268ab99330d28'
RESULT_NATIVE = 'a7b1a824263d026f589eaeaeeedff122b16f4e9efbd2ddd0e8b7c904aabbdbd0'
RESULT_WORDS = 'eef451d5d717ecf075925c34541c6760176570aa3bb16fd053230a9e66f4f65e'
READER_V1 = 'd8c129bc6d405e4ec5d2bd2a403fac2381b593f9b4c90b88a4ef9c6ca2f7fc92'
READER_WORDS = '8f22f126045f5b6d06e95d16b81d36f6944d857984cb93ff0a7669f19a9cdf2e'


class PreparedWordSemanticBridgeTests(unittest.TestCase):
    def test_all_and_only_exact_forward_semantic_transitions(self):
        pins = (RESULT_V1, RESULT_NATIVE, RESULT_WORDS)
        for i, old in enumerate(pins):
            for j, new in enumerate(pins):
                with self.subTest(old=i, new=j), patch.object(adapter, 'sha', side_effect=(old, new)):
                    if i < j:
                        adapter.check_prepared_effect_helper_compatibility(
                            'catalogue/imported_result_contracts.py', b'old inert', b'new inert')
                    else:
                        with self.assertRaises(ValueError):
                            adapter.check_prepared_effect_helper_compatibility(
                                'catalogue/imported_result_contracts.py', b'old inert', b'new inert')

    def test_unknown_mutants_and_wrong_module_fail_closed(self):
        for old, new in ((RESULT_V1, '0'*64), ('0'*64, RESULT_WORDS),
                         (RESULT_NATIVE, 'f'*64), (RESULT_WORDS, RESULT_NATIVE)):
            with self.subTest(old=old, new=new), patch.object(adapter, 'sha', side_effect=(old, new)):
                with self.assertRaises(ValueError):
                    adapter.check_prepared_effect_helper_compatibility(
                        'catalogue/imported_result_contracts.py', b'old inert', b'new inert')
        for name in ('catalogue/node_identity_contracts.py', 'catalogue/unknown.py'):
            with self.subTest(name=name), patch.object(adapter, 'sha', side_effect=(RESULT_NATIVE, RESULT_WORDS)):
                with self.assertRaises(ValueError):
                    adapter.check_prepared_effect_helper_compatibility(name, b'old inert', b'new inert')

    def test_current_semantic_bytes_and_identical_known_helper_route(self):
        raw = Path(q.__file__).with_name('imported_result_contracts.py').read_bytes()
        self.assertEqual(q.sha(raw), RESULT_WORDS)
        adapter.check_prepared_effect_helper_compatibility('catalogue/imported_result_contracts.py', raw, raw)
        with self.assertRaises(ValueError):
            adapter.check_prepared_effect_helper_compatibility('catalogue/unknown.py', raw, raw)

    def test_fixed42_read_owner_records_actual_approved_successor_only(self):
        original = q.file_hash
        for pin in (READER_V1, READER_WORDS):
            def fake(path):
                return pin if Path(path).name == 'public_batch_adapter.py' else original(path)
            with self.subTest(pin=pin), patch.object(q, 'file_hash', side_effect=fake):
                closure = cohort.additional_code()
                self.assertEqual(closure[str(Path(adapter.__file__).resolve())], pin)
                self.assertEqual(len(closure), 12)
        with patch.object(q, 'file_hash', side_effect=lambda path:
                          '0'*64 if Path(path).name == 'public_batch_adapter.py' else original(path)):
            with self.assertRaises(ValueError): cohort.additional_code()


if __name__ == '__main__':
    unittest.main()
