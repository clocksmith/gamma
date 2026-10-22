"""Synthetic parser/inventory tests. Never execute candidate snippets."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('block_inventory', ROOT/'inventory.py')
inv = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inv)


def row(text, variant='synthetic-1', pid=1):
    raw = text.encode()
    return raw, {'language': 'python', 'problem_id': pid, 'variant_id': variant,
                 'source_sha256': inv.digest(raw), 'qualification': {'status': 'unknown'}}


def scan(text, **kwargs):
    return inv.build([row(text, **kwargs)])['occurrences']


def op(text, operation):
    return [x for x in scan(text) if x['operation'] == operation]


class InventoryTests(unittest.TestCase):
    def test_dense_count_complete_statements(self):
        source = 'def f(values, n):\n    counts = [0] * n\n    for x in values:\n        counts[x] += 1\n'
        rows = scan(source)
        self.assertEqual([x['operation'] for x in rows], ['dense_counter_init','dense_counter_increment'])
        self.assertEqual(rows[1]['literal'], 'counts[x] += 1')
        self.assertEqual(rows[1]['roles'], {'counter':'counts','index':'x'})

    def test_no_dense_role_without_initializer(self):
        self.assertEqual(scan('def f(counts, key):\n    counts[key] += 1\n'), [])

    def test_no_false_zero_bool_initializer(self):
        self.assertEqual(scan('def f(n, i):\n    counts = [False] * n\n    counts[i] += 1\n'), [])

    def test_sparse_map_distinct_contract(self):
        source = 'def f(key):\n    counts = {}\n    counts[key] = counts.get(key, 0) + 1\n'
        rows = scan(source)
        self.assertEqual([x['operation'] for x in rows], ['sparse_counter_init','sparse_counter_increment'])
        self.assertNotEqual(rows[0]['contract_id'], rows[1]['contract_id'])
        self.assertIn('key', rows[1]['bindings']['syntactic_reads'])

    def test_sparse_defaults_keys_and_container_must_match(self):
        for update in ['counts[k] = counts.get(k, 1) + 1', 'counts[k] = other.get(k, 0) + 1',
                       'counts[k] = counts.get(j, 0) + 1', 'counts[k] = counts.get(k, False) + 1']:
            self.assertEqual(op('def f(counts,other,k,j):\n    '+update+'\n', 'sparse_counter_increment'), [])

    def test_queue_whole_sibling_block(self):
        source = 'def f(start):\n    q = [start]\n    head = 0\n    while head < len(q):\n        item = q[head]\n        head += 1\n        q.append(item)\n'
        rows = scan(source)
        self.assertEqual([x['operation'] for x in rows], ['queue_init','queue_head_init','queue_read_advance','queue_append'])
        block = rows[2]
        self.assertEqual(block['literal'], 'item = q[head]\n        head += 1')
        self.assertEqual(block['span']['node_types'], ['Assign','AugAssign'])
        self.assertIn('head', block['bindings']['syntactic_reads'])
        self.assertIn('head', block['bindings']['syntactic_writes'])

    def test_queue_no_cross_body_join(self):
        text = 'def f(q,h,ok):\n    if ok:\n        x=q[h]\n    h+=1\n'
        self.assertEqual(op(text,'queue_read_advance'), [])

    def test_queue_no_intervening_statement(self):
        text = 'def f(q,h):\n    x=q[h]\n    y=2\n    h+=1\n'
        self.assertEqual(op(text,'queue_read_advance'), [])

    def test_queue_binding_collision_rejected(self):
        for text in ('q=q[h]\nh+=1', 'h=q[h]\nh+=1', 'x=q[q]\nq+=1'):
            self.assertEqual(op('def f(q,h):\n    '+text.replace('\n','\n    ')+'\n','queue_read_advance'), [])

    def test_nested_scope_does_not_supply_initializer(self):
        text = 'def f(n):\n    counts=[0]*n\n    def g(k):\n        counts[k]+=1\n'
        self.assertEqual(scan(text), [])

    def test_nested_function_scanned_separately(self):
        text = 'def f():\n    def g(q,h):\n        x=q[h]\n        h+=1\n'
        rows = op(text,'queue_read_advance')
        self.assertEqual(len(rows),1)
        self.assertEqual(rows[0]['context']['function'], 'g')

    def test_distinct_bucket_init_not_alias_repetition(self):
        text = 'def f(n):\n    adj=[]\n    for vertex in range(n):\n        adj.append([])\n'
        self.assertEqual(len(op(text,'adjacency_init')),1)
        self.assertEqual(op('def f(n):\n    adj=[[]]*n\n','adjacency_init'), [])

    def test_bucket_init_loop_target_collision(self):
        text = 'def f(n):\n    adj=[]\n    for adj in range(n):\n        adj.append([])\n'
        self.assertEqual(op(text, 'adjacency_init'), [])

    def test_weighted_and_unweighted_pairs_split(self):
        text = 'def f(adj,u,v,w):\n    adj[u].append(v)\n    adj[v].append(u)\n    adj[u].append([v,w])\n    adj[v].append([u,w])\n'
        rows = scan(text)
        self.assertEqual(sum(r['operation']=='edge_unweighted_pair' for r in rows),1)
        self.assertEqual(sum(r['operation']=='edge_weighted_pair' for r in rows),1)
        weighted = next(r for r in rows if r['operation']=='edge_weighted_pair')
        self.assertEqual(weighted['roles']['weight'],'w')

    def test_nonreciprocal_or_different_weight_not_pair(self):
        for second in ('adj[u].append(u)', 'other[v].append(u)', 'adj[v].append([u,w+1])'):
            first = 'adj[u].append([v,w])' if '[u,w' in second else 'adj[u].append(v)'
            rows = scan('def f(adj,other,u,v,w):\n    '+first+'\n    '+second+'\n')
            self.assertFalse(any(r['operation'].startswith('edge_') for r in rows))

    def test_single_arc_does_not_claim_global_directed_graph(self):
        record = op('def f(adj,u,v):\n    adj[u].append(v)\n','arc_unweighted')[0]
        self.assertIn('not proof', ' '.join(record['contract']['domain']))

    def test_exact_crlf_multiline_and_unicode_offsets(self):
        text = 'def f(q, head):\r\n    label = "Ω"; item = q[head]\r\n    # retained comment\r\n    head += 1\r\n'
        record = op(text,'queue_read_advance')[0]
        raw = text.encode()
        span = record['span']
        self.assertEqual(raw[span['start_byte']:span['end_byte']].decode(), record['literal'])
        self.assertEqual(record['literal'], 'item = q[head]\r\n    # retained comment\r\n    head += 1')
        self.assertEqual(span['start_byte'], len('def f(q, head):\r\n    label = "Ω"; '.encode()))

    def test_semicolon_siblings_complete_nodes(self):
        record = op('def f(q,h):\n    x=q[h]; h+=1\n','queue_read_advance')[0]
        self.assertEqual(record['literal'],'x=q[h]; h+=1')

    def test_alpha_proposal_not_literal_identity(self):
        a = op('def f(q,h):\n    x=q[h]\n    h+=1\n','queue_read_advance')[0]
        b = op('def g(buffer,index):\n    result=buffer[index]\n    index+=1\n','queue_read_advance')[0]
        self.assertNotEqual(a['literal_id'], b['literal_id'])
        self.assertEqual(a['macro_proposal_id'], b['macro_proposal_id'])
        self.assertIn('not free', b['encoding']['macro'])

    def test_constants_preserved_in_macro_proposal(self):
        text = 'def f(k):\n    c=[0]*26\n    c[k]+=1\n'
        a = op(text,'dense_counter_init')[0]
        b = op(text.replace('*26','*27'),'dense_counter_init')[0]
        self.assertNotEqual(a['macro_proposal_id'],b['macro_proposal_id'])

    def test_source_location_not_component_identity(self):
        source = 'def f(q,h):\n    x=q[h]\n    h+=1\n'
        a = op(source,'queue_read_advance')[0]
        b = op('\n'+source,'queue_read_advance')[0]
        self.assertEqual(a['literal_id'],b['literal_id'])
        self.assertNotEqual(a['occurrence_id'],b['occurrence_id'])

    def test_source_hash_and_language_fail_closed(self):
        raw, identity = row('def f():\n    x={}\n')
        with self.assertRaises(ValueError): inv.occurrences(raw+b'\n',identity)
        identity['language']='javascript'
        with self.assertRaises(ValueError): inv.occurrences(raw,identity)

    def test_malformed_source_fail_closed(self):
        with self.assertRaises(SyntaxError): scan('def broken(:\n')

    def test_duplicate_and_order_determinism(self):
        a=row('def f():\n    x={}\n','one',1)
        b=row('def g():\n    y={}\n','two',2)
        self.assertEqual(inv.build([a,b]),inv.build([b,a]))
        with self.assertRaises(ValueError): inv.build([a,a])

    def test_candidate_source_never_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory)/'must-not-exist'
            text = f'open({str(marker)!r},"w").write("bad")\ndef f():\n    x={{}}\n'
            self.assertEqual(len(scan(text)),1)
            self.assertFalse(marker.exists())

    def test_effects_calls_and_claims_remain_unknown(self):
        record = op('def f(c):\n    c[key()] = c.get(key(),0)+1\n','sparse_counter_increment')[0]
        self.assertIn('key',record['bindings']['calls_needing_resolution'])
        self.assertIn('stable', ' '.join(record['contract']['domain']))
        doc=inv.build([row('def f():\n    x={}\n')])
        self.assertEqual(doc['candidate_executions'],0)
        self.assertEqual(doc['new_qualifications'],0)
        self.assertIsNone(doc['coverage'])
        self.assertIsNone(doc['encoded_bits'])

    def test_catalog_code_pin_precedes_import(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fake.py'; marker=Path(directory)/'bad'
            path.write_text(f'open({str(marker)!r},"w").write("bad")')
            with self.assertRaises(ValueError): inv.load_sources([],path)
            self.assertFalse(marker.exists())


if __name__ == '__main__': unittest.main()
