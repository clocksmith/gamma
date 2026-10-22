"""Independent synthetic source-as-data regressions; no candidate execution."""
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location('block_inventory_review', ROOT / 'inventory.py')
inv = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(inv)


def scan(source):
    raw = source.encode('utf-8')
    identity = {'language': 'python', 'problem_id': 1,
                'variant_id': inv.digest(raw), 'source_sha256': inv.digest(raw),
                'qualification': {'status': 'unknown'}}
    return inv.occurrences(raw, identity)


def operations(source, operation):
    return [r for r in scan(source) if r['operation'] == operation]


class IndependentReviewTests(unittest.TestCase):
    def test_nested_expression_scopes_are_omitted_but_queue_block_remains(self):
        for expression in ('lambda x: x', '[x for x in values]',
                           '{x for x in values}', '{x: x for x in values}',
                           '(x for x in values)'):
            with self.subTest(expression=expression):
                source = ('def f(values, h):\n    q = [' + expression + ']\n'
                          '    item = q[h]\n    h += 1\n')
                self.assertEqual(operations(source, 'queue_init'), [])
                self.assertEqual(len(operations(source, 'queue_read_advance')), 1)

    def test_bound_lambda_and_free_capture_never_share_macro_identity(self):
        prefix = 'def f(q, h, free):\n    q = ['
        suffix = ']\n    item = q[h]\n    h += 1\n'
        bound = operations(prefix + 'lambda x: x' + suffix, 'queue_init')
        captured = operations(prefix + 'lambda x: free' + suffix, 'queue_init')
        # Rejecting unsupported scopes or separating their identities are valid.
        bound_ids = {r['macro_proposal_id'] for r in bound if r.get('macro_proposal_id')}
        captured_ids = {r['macro_proposal_id'] for r in captured if r.get('macro_proposal_id')}
        self.assertFalse(bound_ids & captured_ids)

    def test_cr_only_source_spans_are_exact(self):
        source = 'def f(q, h):\r    item = q[h]\r    h += 1\r'
        record = operations(source, 'queue_read_advance')[0]
        raw = source.encode('utf-8')
        span = record['span']
        self.assertEqual(raw[span['start_byte']:span['end_byte']].decode('utf-8'),
                         'item = q[h]\r    h += 1')

    def test_unicode_identifier_offsets_are_bytes_not_characters(self):
        source = 'def f(q, h):\n    Ω = "😀"; élément = q[h]; h += 1\n'
        record = operations(source, 'queue_read_advance')[0]
        self.assertEqual(record['span']['start_byte'],
                         len('def f(q, h):\n    Ω = "😀"; '.encode('utf-8')))
        self.assertEqual(record['literal'], 'élément = q[h]; h += 1')
        self.assertEqual(record['literal_utf8_bytes'], len(record['literal'].encode('utf-8')))

    def test_multiline_expression_keeps_interior_comment(self):
        source = ('def f(q, h):\n    item = q[\n'
                  '        h  # exact source comment\n    ]\n    h += 1\n')
        record = operations(source, 'queue_read_advance')[0]
        self.assertEqual(record['literal'],
                         'item = q[\n        h  # exact source comment\n    ]\n    h += 1')

    def test_literal_identity_changes_with_interior_comment_not_macro_shape(self):
        source = 'def f(q, h):\n    item = q[h]\n    # first\n    h += 1\n'
        a = operations(source, 'queue_read_advance')[0]
        b = operations(source.replace('# first', '# second'), 'queue_read_advance')[0]
        self.assertNotEqual(a['literal_id'], b['literal_id'])
        self.assertEqual(a['macro_proposal_id'], b['macro_proposal_id'])

    def test_exception_handler_and_else_lists_are_separate(self):
        source = ('def f(q, h):\n    try:\n        item = q[h]\n'
                  '    except Exception:\n        h += 1\n'
                  '    else:\n        h += 1\n')
        self.assertEqual(operations(source, 'queue_read_advance'), [])

    def test_alias_role_is_preserved_in_proposal_identity(self):
        a = operations('def f(adj, u, v):\n    adj[u].append(v)\n', 'arc_unweighted')[0]
        b = operations('def f(adj, u):\n    adj[u].append(u)\n', 'arc_unweighted')[0]
        self.assertNotEqual(a['macro_proposal_id'], b['macro_proposal_id'])

    def test_operation_and_contract_identities_remain_separate(self):
        source = ('def f(q, h):\n    q = []\n    h = 0\n'
                  '    item = q[h]\n    h += 1\n')
        rows = scan(source)
        self.assertEqual(len({r['contract_id'] for r in rows}), len(rows))
        self.assertTrue(all(r['qualification'].startswith('unknown') for r in rows))
        self.assertTrue(all(r['encoding']['macro'].startswith('proposal only') for r in rows))


if __name__ == '__main__':
    unittest.main()
