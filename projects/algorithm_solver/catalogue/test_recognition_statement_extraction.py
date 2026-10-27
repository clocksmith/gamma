import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from . import recognition_statement_extraction as x
from . import recognition_description_schema as s
from . import test_boundary_policy as bp


class StatementExtractionTests(unittest.TestCase):
    def setUp(self):
        self.row = {'problem_id': 'leetcode:1', 'title': 'Synthetic statement', 'aliases': ['lc:synthetic'],
                    'sha256': 'a'*64, 'original_path': '/approved/statements/1.md'}

    def project(self, text):
        d, a = x.normalize_statement(text, self.row, policy_sha256='b'*64)
        s.validate(d, authorized_ids={'leetcode:1'}, exact_aliases={'lc:synthetic': 'leetcode:1'},
                   expected_policy_sha256='b'*64)
        return d, a

    def test_examples_answers_hints_and_solutions_are_not_rendered(self):
        html = '<p>Given a list of integers.</p><p>Return the maximum.</p><p>Example 1:</p>' \
               '<pre>Input: [1,2] Output: EXAMPLE_ANSWER</pre><p>Explanation: EXPLANATION</p>' \
               '<p>Constraints:</p><ul><li>1 &lt;= n &lt;= 10<sup>5</sup></li></ul>' \
               '<h2>Solution</h2><p>SOLUTION_BODY</p><p>Constraints:</p><p>SHOULD_NOT_REENTER</p>'
        d, audit = self.project(html)
        text = s.render(d)
        for secret in ('EXAMPLE_ANSWER', 'EXPLANATION', 'SOLUTION_BODY', 'SHOULD_NOT_REENTER'):
            self.assertNotIn(secret, text)
        self.assertIn('10^(5)', text)
        self.assertEqual(d['fields']['effects']['status'], 'unknown')
        self.assertGreater(audit['excluded']['example_blocks'], 0)

    def test_hypothetical_operations_do_not_become_mutation_contract(self):
        d, _ = self.project('<p>Given a string.</p><p>In one operation you can modify one character.</p>'
                            '<p>Return the fewest operations.</p><p>Constraints:</p><p>The string is nonempty.</p>')
        self.assertEqual(d['fields']['effects']['status'], 'unknown')
        self.assertIn('modify one character', s.render(d))

    def test_explicit_inplace_requirement_is_not_inferred(self):
        d, _ = self.project('<p>Given an array.</p><p>You must modify the array in-place.</p>'
                            '<p>Return its new length.</p>')
        self.assertEqual(d['fields']['effects']['status'], 'partial')
        self.assertEqual(d['fields']['effects']['value'], ['You must modify the array in-place.'])

    def test_optional_followup_not_silently_mandatory(self):
        d, a = self.project('<p>Given a list.</p><p>Return its length.</p><p>Example 1:</p>'
                            '<pre>ignored example</pre><p>Constraints:</p><p>List is nonempty.</p>'
                            '<p>Follow up: Can you avoid extra storage?</p>')
        self.assertTrue(a['optional_follow_up_is_not_mandatory'])
        self.assertIn('Follow up:', str(d['fields']['distinguishing_details']['value']))
        self.assertNotIn('Follow up:', str(d['fields']['constraints']['value']))

    def test_does_not_guess_input_types_or_unknown_constraints(self):
        d, _ = self.project('<p>Design a dictionary that supports queries.</p>')
        self.assertEqual(d['fields']['input']['status'], 'unknown')
        self.assertEqual(d['fields']['constraints']['status'], 'unknown')
        self.assertEqual(d['fields']['output']['status'], 'unknown')

    def test_unclassified_field_does_not_claim_fact_absent_from_source(self):
        d, _ = self.project('<p>A list is supplied to the function.</p>'
                            '<p>Return the largest element.</p>')
        self.assertEqual(d['fields']['input']['status'], 'unknown')
        self.assertIn('A list is supplied', s.render(d))
        self.assertIn('Input: Unknown in this description;', s.render(d))
        self.assertNotIn('Unspecified in the available statement', s.render(d))

    def test_same_paragraph_input_and_explicit_output_are_both_recorded(self):
        d, _ = self.project('<p>Given a tree, construct its mirror and return its root.</p>')
        self.assertEqual(d['fields']['input']['status'], 'partial')
        self.assertEqual(d['fields']['output']['status'], 'partial')
        self.assertEqual(d['fields']['input']['value'], d['fields']['output']['value'])

    def test_return_to_location_is_not_guessed_as_api_output(self):
        d, _ = self.project('<p>Given a path.</p><p>Travelers return to their origin.</p>')
        self.assertEqual(d['fields']['output']['status'], 'unknown')

    def test_source_clauses_have_source_selectors(self):
        d, _ = self.project('<p>Given a tree.</p><p>Return its root.</p>')
        for field in d['fields'].values():
            for evidence in field['evidence']:
                self.assertEqual(evidence['source_sha256'], 'a'*64)
                self.assertRegex(evidence['selector'], r'^html\.blocks\[\d+\]$')

    def test_script_and_style_are_not_statement_semantics(self):
        d, _ = self.project('<p>Given a number.</p><script>SCRIPT_SECRET</script><style>STYLE_SECRET</style>'
                            '<p>Return its absolute value.</p>')
        self.assertNotIn('SECRET', s.render(d))

    def test_definition_images_are_flagged_without_inventing_diagram_facts(self):
        d, a = self.project('<p>Given a diagram.</p><img src="definition.png">'
                            '<p>Return the requested count.</p><p>Example 1:</p><img src="example.png">')
        self.assertEqual(a['excluded']['images'], 2)
        self.assertEqual(a['excluded']['definition_images'], 1)
        self.assertTrue(a['explicit_reviewer_attention'])
        self.assertNotIn('definition.png', s.render(d))

    def test_no_definition_and_malformed_math_fail_closed(self):
        with self.assertRaises(ValueError):
            self.project('<p>Example 1:</p><pre>example only</pre>')
        with self.assertRaises(ValueError):
            self.project('<p>Given 10<sup>5</p>')

    def test_deterministic_projection_and_original_title(self):
        html = '<p>Given&nbsp;a list.</p><p>Return the number of elements.</p>'
        a, _ = self.project(html); b, _ = self.project(html)
        self.assertEqual(a, b)
        self.assertEqual(s.render(a), s.render(b))
        self.assertTrue(s.render(a).startswith('Synthetic statement\n'))
        self.assertNotIn('leetcode:1', s.render(a))


class StatementAcquisitionTests(unittest.TestCase):
    """Synthetic payloads only; exercise the live gate and exact locator order."""
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        raw, pins = bp.BoundaryPolicyTests().fixture()
        paths = {}
        for name, data in raw.items():
            p = self.root / (name + '.json')
            p.write_bytes(data)
            paths[name] = str(p)
        gate = {'schema': 'gamma.boundary-gate-config.v1', 'artifact_paths': paths,
                'trusted_hashes': pins}
        p = self.root / 'gate.json'
        p.write_text(json.dumps(gate))
        self.plan = {'batch_id': 'synthetic', 'boundary_gate': {
            'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()},
            'expected_policy_sha256': pins['policy'], 'rows': []}
        for number, alias in ((1, 'lc:first'), (2, 'lc:second')):
            p = self.root / (str(number) + '.md')
            data = b'<p>Given a list.</p><p>Return its length.</p>'
            p.write_bytes(data)
            self.plan['rows'].append({'problem_id': 'leetcode:' + str(number),
                'title': 'Synthetic statement ' + str(number), 'aliases': [alias],
                'path': str(p), 'original_path': '/approved/' + p.name,
                'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)})

    def build(self):
        return x.build_batch(self.plan, source_root=self.root)

    def test_gate_immediately_precedes_each_exact_payload_open(self):
        events = []
        gate, read = x.boundary_policy.authorize_before_open, x.authority_bytes
        def authorize(pid, *args, **kwargs):
            events.append(('gate', pid))
            self.assertEqual(kwargs['payload_kind'], 'statement')
            return gate(pid, *args, **kwargs)
        def opened(spec, roots):
            pid = 'leetcode:' + Path(spec['path']).stem
            self.assertEqual(events[-1], ('gate', pid))
            events.append(('read', pid))
            return read(spec, roots)
        with patch.object(x.boundary_policy, 'authorize_before_open', side_effect=authorize), \
                patch.object(x, 'authority_bytes', side_effect=opened):
            got = self.build()
        self.assertEqual(events, [('gate', 'leetcode:1'), ('read', 'leetcode:1'),
                                  ('gate', 'leetcode:2'), ('read', 'leetcode:2')])
        self.assertEqual(got['summary']['descriptions'], 2)
        self.assertFalse(got['encoder_executed'])

    def test_reserved_unresolved_and_outside_never_open(self):
        for number in (3, 4, 5, 6):
            row = copy.deepcopy(self.plan['rows'][0])
            row.update(problem_id='leetcode:' + str(number), aliases=[],
                       path=str(self.root / (str(number) + '.md')),
                       original_path='/approved/' + str(number) + '.md')
            self.plan['rows'] = [row]
            with patch.object(x, 'authority_bytes', side_effect=AssertionError('must not open')):
                with self.assertRaises(PermissionError):
                    self.build()

    def test_locator_alias_duplicate_and_stale_policy_fail_before_open(self):
        original = copy.deepcopy(self.plan)
        for change in ('locator', 'alias', 'duplicate', 'policy'):
            self.plan = copy.deepcopy(original)
            if change == 'locator':
                self.plan['rows'][0]['original_path'] = '/approved/2.md'
            elif change == 'alias':
                self.plan['rows'][0]['aliases'] = ['lc:second']
            elif change == 'duplicate':
                self.plan['rows'].append(copy.deepcopy(self.plan['rows'][0]))
            else:
                self.plan['expected_policy_sha256'] = 'f' * 64
            with patch.object(x, 'authority_bytes', side_effect=AssertionError('must not open')):
                with self.assertRaises(ValueError):
                    self.build()

    def test_statement_byte_drift_size_and_symlink_rejected(self):
        original = copy.deepcopy(self.plan)
        for change in ('hash', 'size', 'symlink'):
            self.plan = copy.deepcopy(original)
            if change == 'hash':
                self.plan['rows'][0]['sha256'] = 'f' * 64
            elif change == 'size':
                self.plan['rows'][0]['bytes'] += 1
            else:
                p = Path(self.plan['rows'][0]['path'])
                target = self.root / 'alternate.md'
                p.rename(target)
                p.symlink_to(target)
            with self.assertRaises((ValueError, PermissionError, OSError)):
                self.build()


if __name__ == '__main__':
    unittest.main()
