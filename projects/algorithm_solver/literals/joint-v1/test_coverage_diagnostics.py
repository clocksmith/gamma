"""Synthetic pool/selection diagnoses; no candidate execution or fitting."""
import json
import os
from pathlib import Path
import unittest

import coverage_diagnostics as diagnostic
import idiom_pilot as pilot


class CoverageDiagnostics(unittest.TestCase):
    def test_missing_identifier_and_number_spans_are_hashed_not_exposed(self):
        result = diagnostic.source_analysis('abc+37', ['+'], tokens=[
            {'start': 0, 'end': 3, 'category': 'identifier'},
            {'start': 3, 'end': 4, 'category': 'operator'},
            {'start': 4, 'end': 6, 'category': 'number'}])
        self.assertFalse(result['full_pool_complete'])
        self.assertTrue(result['candidate_text_scarcity'])
        self.assertEqual(result['missing_characters_by_category'], {'identifier': 3, 'number': 2})
        self.assertEqual(result['unsupported_spans'][1]['start'], 4)
        self.assertEqual(result['unsupported_spans'][1]['text_sha256'], diagnostic.sha(b'37'))
        self.assertTrue(all(not {'text', 'value'} & gap.keys() for gap in result['unsupported_spans']))

    def test_partial_identifier_match_is_boundary_only_failure(self):
        result = diagnostic.source_analysis('longer+2', ['long', 'er+2'], boundaries={0, 6, 7, 8},
            tokens=[{'start': 0, 'end': 6, 'category': 'identifier'}])
        self.assertTrue(result['unrestricted_pool_complete'])
        self.assertTrue(result['boundary_only_obstruction'])
        self.assertFalse(result['candidate_text_scarcity'])

    def test_covering_every_character_does_not_prove_a_connected_parse(self):
        result = diagnostic.source_analysis('abc', ['ab', 'bc'])
        self.assertFalse(result['full_pool_complete'])
        self.assertEqual(result['unsupported_spans'], [])
        self.assertTrue(result['path_connectivity_obstruction'])
        self.assertTrue(result['unrestricted_path_connectivity_obstruction'])
        self.assertFalse(result['candidate_text_scarcity'])

    def test_individual_path_is_constructive_but_not_shared_dictionary_proof(self):
        result = diagnostic.source_analysis('abab!', ['ab', '!'])
        budget = diagnostic.budget_diagnosis(result, 4, False)
        self.assertEqual(result['minimum_selection_path_distinct_entries'], 2)
        self.assertTrue(budget['selection_search_gap_witness'])
        self.assertFalse(budget['shared_dictionary_feasibility_proven'])

    def test_over_budget_shortest_path_is_not_an_infeasibility_proof(self):
        words = [f'a{i:x}' for i in range(17)]
        text = ''.join(words)
        result = diagnostic.source_analysis(text, words + sorted(set(text)))
        budget = diagnostic.budget_diagnosis(result, 4, False)
        self.assertTrue(budget['minimum_selection_path_over_budget_only'])
        self.assertFalse(budget['necessary_forced_slots_exceed_budget'])
        # The longer singleton path is a <=16-entry witness, despite the shorter
        # minimum-selection path using17 distinct multichar entries.
        self.assertLessEqual(len(set(text)), 16)

    def test_forced_slots_supply_a_necessary_bound_for_this_pool_only(self):
        text = 'abcdefghijklmnopq'
        result = diagnostic.source_analysis(text, list(text))
        self.assertEqual(result['necessary_forced_entry_count'], 17)
        self.assertTrue(diagnostic.budget_diagnosis(result, 4, False)['necessary_forced_slots_exceed_budget'])

    def test_shared_budget_lower_bound_and_constructive_union_are_separate(self):
        pool = list('abcdefghijklmnopq')
        analyses = {(i, 'a'): diagnostic.source_analysis(letter * 2, pool)
                    for i, letter in enumerate(pool)}
        result = diagnostic.shared_budget_bounds(analyses)
        self.assertEqual(result['full_pool_representable_problems'], 17)
        self.assertEqual(result['necessary_shared_entry_lower_bound'], 17)
        self.assertEqual(result['constructive_path_union_entry_upper_bound'], 17)
        self.assertTrue(all(a['minimum_selection_path_distinct_entries'] <= 16 for a in analyses.values()))

    def test_shared_forced_bound_intersects_alternative_variants(self):
        analyses = {(1, 'a'): diagnostic.source_analysis('aa', ['a']),
                    (1, 'b'): diagnostic.source_analysis('bb', ['b'])}
        result = diagnostic.shared_budget_bounds(analyses)
        self.assertEqual(result['necessary_shared_entry_lower_bound'], 0)
        self.assertEqual(result['constructive_path_union_entry_upper_bound'], 1)
        self.assertEqual(result['full_pool_representable_problems'], 1)

    def test_occurrence_budget_invalid_tokens_and_boundaries_fail_closed(self):
        for kwargs in [{'boundaries': {1, 2}}, {'tokens': [{'start': 0, 'end': 9, 'category': 'identifier'}]},
                       {'tokens': [{'start': 0, 'end': 1, 'category': 'invented'}]}]:
            with self.assertRaises(ValueError): diagnostic.source_analysis('ab', ['a', 'b'], **kwargs)
        with self.assertRaises(ValueError): diagnostic.source_analysis('x', ['x', 'x'])

    def test_javascript_token_intervals_use_codepoints_and_report_no_values(self):
        node = os.environ.get('GAMMA_TEST_NODE')
        if not node: self.skipTest('explicit existing Node required')
        runtime = Path(node)
        sources = {1: {'a': 'const value="\U0001d49c"; const count=37; const re=/[a-z]/i;'}}
        parsed = pilot.syntactic_spans(sources, 'javascript', runtime, pilot.digest(runtime), include_tokens=True)
        tokens = parsed['tokens']['1/a']
        self.assertTrue(all(set(t) == {'start', 'end', 'category'} for t in tokens))
        number = next(t for t in tokens if t['category'] == 'number')
        text = sources[1]['a']
        self.assertEqual(text[number['start']:number['end']], '37')
        regexp = next(t for t in tokens if t['category'] == 'regexp')
        self.assertEqual(text[regexp['start']:regexp['end']], '/[a-z]/i')
        self.assertNotIn(chr(0x1D49C), json.dumps(tokens, ensure_ascii=False))

    def test_widths_reuse_analysis_and_one_bad_variant_does_not_exclude_problem(self):
        sources = {1: {'a': 'ab!', 'b': 'xab!'}}
        parsed = {'boundaries': {'1/a': [0, 2, 3], '1/b': [0, 1, 3, 4]},
                  'tokens': {'1/a': [], '1/b': []}, 'features': {'1/a': {}, '1/b': {}}}
        rows = []
        for width in (4, 5):
            state = pilot.joint.evaluate(sources, ['ab', '!'], width, alphabet=[], allow_partial=True,
                                        source_objective='compact')
            final = {k: state[k] for k in ('coverage', 'selections', 'singleton_bits', 'literal_bits', 'package_bytes')}
            final['dictionary'] = state['vocab']
            rows.append({'arm': 'punctuation_fallback', 'pool': 'compression_fragments',
                         'width': width, 'final': final})
        result = diagnostic.diagnose(sources, parsed, {'compression_fragments': ['ab']}, {'rows': rows})
        self.assertEqual(len(result['pool_source_analyses']), 2)
        self.assertEqual(len(result['records']), 4)
        for row in result['aggregate']['rows']:
            self.assertEqual(row['counts']['full_pool_complete'], 1)
            self.assertEqual(row['counts']['all_variants_full_pool_incomplete'], 0)

    def test_pool_only_does_not_invent_a_measured_search_gap(self):
        sources = {1: {'a': 'ab!'}}
        parsed = {'boundaries': {'1/a': [0, 2, 3]}, 'tokens': {'1/a': []}, 'features': {'1/a': {}}}
        result = diagnostic.diagnose(sources, parsed, {'compression_fragments': ['ab']})
        self.assertFalse(result['aggregate']['retained_dictionary_comparison_performed'])
        self.assertTrue(all(r['counts']['selected_complete'] is None for r in result['aggregate']['rows']))
        self.assertTrue(all(r['counts']['selection_search_gap_witness'] == 0 for r in result['aggregate']['rows']))


if __name__ == '__main__':
    unittest.main()
