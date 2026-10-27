"""Synthetic-only checks: no statements, implementations, cases or models opened."""
import copy
import hashlib
import json
import unittest

from . import recognition_description_schema as s


class DescriptionSchemaTests(unittest.TestCase):
    def setUp(self):
        self.pid = 'leetcode:1'
        self.title = 'Synthetic Array Contract'
        self.policy = 'b' * 64
        self.source = 'c' * 64
        self.aliases = {self.pid: self.pid, 'lc:synthetic-array-contract': self.pid}
        fields = {'Objective': 'Report the declared item count.',
                  'Result': {'type': 'integer', 'semantics': 'The declared item count.'},
                  'Input domain': ['The input is a nonempty integer array.'],
                  'Ordered interface': {'parameters': ['items'], 'entrypoint': 'solve'}}
        text = self.title + '\n' + ''.join(k + ': ' + json.dumps(v) + '\n' for k, v in fields.items())
        self.legacy = {'problem_id': self.pid, 'text': text, 'document_sha256': s.text_hash(text),
                       'authority': {'knowledge_class': 'development-authored-description-candidate'}}
        self.row = s.project_legacy(self.legacy, title=self.title, aliases=list(self.aliases),
                                   source_sha256=self.source, policy_sha256=self.policy)

    def validate(self, row=None, **changes):
        args = dict(authorized_ids={self.pid}, exact_aliases=self.aliases,
                    expected_policy_sha256=self.policy)
        args.update(changes)
        return s.validate(self.row if row is None else row, **args)

    def test_exact_six_fields_and_explicit_unknowns(self):
        result = self.validate()
        self.assertEqual(set(self.row['fields']), set(s.FIELDS))
        self.assertEqual(result['known_fields'], 4)
        self.assertEqual(result['unknown_fields'], ['effects', 'distinguishing_details'])
        self.assertFalse(result['qualified'])
        self.assertFalse(result['publication_authorized'])

    def test_legacy_projection_preserves_input_and_semantics_without_mutation(self):
        before = copy.deepcopy(self.legacy)
        projected = s.project_legacy(self.legacy, title=self.title, aliases=list(self.aliases),
                                     source_sha256=self.source, policy_sha256=self.policy)
        self.assertEqual(before, self.legacy)
        self.assertEqual(projected['fields']['intent']['value'], 'Report the declared item count.')
        self.assertEqual(projected['fields']['input']['value']['parameters'], ['items'])
        self.assertEqual(projected['fields']['constraints']['value'], ['The input is a nonempty integer array.'])
        self.assertEqual(projected['semantic_review_status'], 'source-preserving-projection')

    def test_render_is_deterministic_and_bindings_recompute(self):
        a = self.validate()
        text = s.render(self.row)
        self.assertEqual(a['document_sha256'], hashlib.sha256(text.encode()).hexdigest())
        self.assertEqual(a['bytes'], len(text.encode()))
        self.assertEqual(a, self.validate(copy.deepcopy(self.row)))
        self.assertEqual(text.splitlines()[0], self.title)
        self.assertTrue(text.endswith('\n'))

    def test_identity_permission_and_evidence_are_not_ranking_features(self):
        before = s.render(self.row)
        self.row['problem_id'] = 'leetcode:2'
        self.row['aliases'] = ['leetcode:2']
        self.row['permission']['policy_sha256'] = 'd' * 64
        self.row['provenance']['source_locator'] = 'another trusted location'
        self.assertEqual(before, s.render(self.row))
        self.assertNotIn(self.source, before)
        self.assertNotIn(self.policy, before)
        self.assertNotIn('development-authored', before)

    def test_unknown_is_not_an_inferred_negative_or_unconstrained_claim(self):
        self.assertEqual(self.row['fields']['effects']['value'], None)
        self.assertIn(s.UNKNOWN, s.render(self.row))
        self.row['fields']['effects']['value'] = False
        with self.assertRaisesRegex(ValueError, 'unknown is not'):
            self.validate()

    def test_unknown_metadata_does_not_assert_source_omission(self):
        field = s.unknown_field()
        self.assertIn('not_assigned_in_this_description', field['unknown_reason'])
        self.assertIn('no source-absence inference', field['unknown_reason'])
        self.assertNotIn('not_stated', field['unknown_reason'])

    def test_reviewed_incomplete_is_distinct_and_never_qualification(self):
        self.row['semantic_review_status'] = 'independently-reviewed-incomplete'
        checked = self.validate()
        self.assertFalse(checked['qualified'])
        self.assertFalse(checked['publication_authorized'])
        summary = s.summarize([self.row])
        self.assertEqual(summary['semantic_review_counts'], {'independently-reviewed-incomplete': 1})
        self.row['semantic_review_status'] = 'fully-qualified'
        with self.assertRaisesRegex(ValueError, 'review scope'):
            self.validate()

    def test_unknown_never_has_evidence_or_silent_empty_reason(self):
        for name, value in [('evidence', [{'source_sha256': self.source}]), ('unknown_reason', '')]:
            row = copy.deepcopy(self.row)
            row['fields']['effects'][name] = value
            with self.assertRaises(ValueError):
                self.validate(row)

    def test_missing_or_extra_semantic_fields_fail(self):
        for mode in ('missing', 'extra'):
            row = copy.deepcopy(self.row)
            if mode == 'missing':
                del row['fields']['effects']
            else:
                row['fields']['solution'] = 'An implementation is not a description.'
            with self.assertRaisesRegex(ValueError, 'all six'):
                self.validate(row)

    def test_reserved_and_unresolved_identities_remain_closed(self):
        with self.assertRaises(PermissionError):
            self.validate(authorized_ids=set())

    def test_canonical_ids_cannot_be_guessed_from_alias(self):
        for value in ('lc:synthetic-array-contract', 'leetcode:01', 'leetcode:0', 'leetcode:1\n'):
            row = copy.deepcopy(self.row)
            row['problem_id'] = value
            with self.assertRaisesRegex(ValueError, 'canonical'):
                self.validate(row)

    def test_aliases_must_be_exact_unambiguous_and_nonduplicated(self):
        for value in ([self.pid, self.pid], ['lc:guessed'], ['lc:other-problem']):
            row = copy.deepcopy(self.row)
            row['aliases'] = value
            with self.assertRaisesRegex(ValueError, 'alias'):
                self.validate(row, exact_aliases={**self.aliases, 'lc:other-problem': 'leetcode:2'})
        with self.assertRaisesRegex(ValueError, 'alias'):
            self.validate(exact_aliases={self.pid: [self.pid, 'leetcode:2']})

    def test_source_permission_does_not_authorize_statement_or_publication(self):
        for key, value in [('payload_kind', 'source'), ('scope', 'qualified-source'),
                           ('publication', 'public'), ('publication', True)]:
            row = copy.deepcopy(self.row)
            row['permission'][key] = value
            with self.assertRaisesRegex(ValueError, 'statement-only'):
                self.validate(row)

    def test_policy_must_match_external_current_pin(self):
        row = copy.deepcopy(self.row)
        row['permission']['policy_sha256'] = 'f' * 64
        with self.assertRaisesRegex(ValueError, 'statement-only'):
            self.validate(row)
        with self.assertRaisesRegex(ValueError, 'external current'):
            self.validate(expected_policy_sha256=None)

    def test_source_availability_or_qualification_flags_cannot_expand_schema(self):
        for key in ('source_availability', 'qualified', 'publication_authorized'):
            row = copy.deepcopy(self.row)
            row[key] = True
            with self.assertRaisesRegex(ValueError, 'exact normalized'):
                self.validate(row)

    def test_solution_guide_and_case_provenance_are_rejected(self):
        for kind in ('solution', 'source', 'guide', 'cases', 'implementation'):
            row = copy.deepcopy(self.row)
            row['provenance']['source_kind'] = kind
            with self.assertRaisesRegex(ValueError, 'statement-bound'):
                self.validate(row)
        for kind in ('source-qualified', 'test-outcome', 'solution-derived'):
            row = copy.deepcopy(self.row)
            row['evidence_class'] = kind
            with self.assertRaisesRegex(ValueError, 'solution/guide/test'):
                self.validate(row)

    def test_known_fields_require_exact_artifact_evidence(self):
        for change in ('hash', 'selector', 'missing'):
            row = copy.deepcopy(self.row)
            field = row['fields']['intent']
            if change == 'hash':
                field['evidence'][0]['source_sha256'] = 'd' * 64
            elif change == 'selector':
                field['evidence'][0]['selector'] = ''
            else:
                field['evidence'] = []
            with self.assertRaises(ValueError):
                self.validate(row)

    def test_field_cannot_upgrade_development_evidence_to_normative(self):
        self.row['fields']['intent']['evidence'][0]['evidence_class'] = 'reviewed-normative-contract'
        with self.assertRaisesRegex(ValueError, 'field evidence'):
            self.validate()

    def test_known_values_must_not_be_blank_or_nonfinite(self):
        for value in ('', '   \t', [], {}, {'maximum': float('nan')}):
            row = copy.deepcopy(self.row)
            row['fields']['intent']['value'] = value
            with self.assertRaises(ValueError):
                self.validate(row)

    def test_document_character_limit_stays_bounded(self):
        self.row['fields']['intent']['value'] = 'x' * s.MAX_TEXT_CHARS
        with self.assertRaisesRegex(ValueError, 'bounded|character limit'):
            self.validate()

    def test_legacy_title_and_document_hash_are_verified(self):
        with self.assertRaisesRegex(ValueError, 'title'):
            s.project_legacy(self.legacy, title='Different', aliases=[], source_sha256=self.source,
                             policy_sha256=self.policy)
        self.legacy['text'] += ' '
        with self.assertRaisesRegex(ValueError, 'UTF-8 hash'):
            s.project_legacy(self.legacy, title=self.title, aliases=[], source_sha256=self.source,
                             policy_sha256=self.policy)

    def test_legacy_duplicate_json_keys_and_nonfinite_values_are_rejected(self):
        for payload in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":Infinity}'):
            doc = copy.deepcopy(self.legacy)
            doc['text'] = doc['text'].replace(json.dumps(['The input is a nonempty integer array.']), payload)
            doc['document_sha256'] = s.text_hash(doc['text'])
            with self.assertRaisesRegex(ValueError, 'duplicate|nonfinite'):
                s.project_legacy(doc, title=self.title, aliases=[], source_sha256=self.source,
                                 policy_sha256=self.policy)

    def test_legacy_unapproved_or_duplicate_labels_are_rejected(self):
        for line in ('Solution: "not allowed"\n', 'Result: "another value"\n'):
            doc = copy.deepcopy(self.legacy)
            doc['text'] += line
            doc['document_sha256'] = s.text_hash(doc['text'])
            with self.assertRaisesRegex(ValueError, 'unapproved/duplicate'):
                s.project_legacy(doc, title=self.title, aliases=[], source_sha256=self.source,
                                 policy_sha256=self.policy)

    def test_legacy_title_only_cannot_be_upgraded(self):
        doc = copy.deepcopy(self.legacy)
        doc['authority']['knowledge_class'] = 'title-only'
        with self.assertRaisesRegex(ValueError, 'upgraded'):
            s.project_legacy(doc, title=self.title, aliases=[], source_sha256=self.source,
                             policy_sha256=self.policy)

    def test_batches_must_be_disjoint_and_summary_preserves_unknowns(self):
        report = s.summarize([self.row])
        self.assertEqual(report['descriptions'], 1)
        self.assertEqual(report['field_states']['effects'], {'unknown': 1})
        self.assertFalse(report['solutions_used_as_authority'])
        self.assertFalse(report['encoder_executed'])
        self.assertFalse(report['publication_authorized'])
        with self.assertRaisesRegex(ValueError, 'disjoint'):
            s.summarize([self.row, copy.deepcopy(self.row)])


if __name__ == '__main__':
    unittest.main()
