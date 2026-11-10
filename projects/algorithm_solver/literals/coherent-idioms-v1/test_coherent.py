import copy
import unittest
import coherent as c
from verifier import verify_accumulator


def record(source, receipt=True):
    sha=c.digest(source.encode())
    return {'source':source,'sha256':sha,'problem_id':'synthetic-'+sha,**({'qualification':{'source_sha256':sha,
        'receipt_sha256':'a'*64,'contract':'synthetic-test-only','status':'passed'}} if receipt else {})}


class CoherentTests(unittest.TestCase):
    def samples(self,lang):
        if lang=='python':
            return {'a':record('def one(xs):\n    total = 0\n    for x in xs:\n        total += x\n    return total\n'),
                    'b':record('def two(xs):\n    total = 1\n    for x in xs:\n        total += x\n    return total\n')}
        return {'a':record('function one(xs) { let total=0; for (const x of xs) { total += x; } return total; }'),
                'b':record('function two(xs) { let total=1; for (const x of xs) { total += x; } return total; }')}

    def test_states_and_exact_spans(self):
        for lang in ('python','javascript'):
            records=self.samples(lang); pool=c.enumerate_candidates(records,lang)
            loops=[x for x in pool if x['kind']=='loop_opening']
            self.assertTrue(loops)
            self.assertIn('for x in xs:' if lang=='python' else 'for (const x of xs) {',[x['literal'] for x in loops])
            updates=[x for x in pool if x['kind']=='accumulator_update' and x['literal']==('total += x' if lang=='python' else 'total += x;')]; self.assertEqual(len(updates),1)
            self.assertEqual(updates[0]['state'],'promising')
            trusted=c.promote(updates[0]); self.assertEqual(trusted['state'],'trusted')
            self.assertFalse(trusted['evidence']['primitive']['full_source_qualification'])
            self.assertEqual(c.promote(loops[0])['state'],'promising')
            for item in pool:
                for p in item['provenance']:
                    self.assertEqual(records[p['source_id']]['source'].encode()[p['start_byte']:p['end_byte']],item['literal'].encode())
            unbound={k:record(v['source'],False) for k,v in records.items()}
            self.assertTrue(all(x['state']=='generated' for x in c.enumerate_candidates(unbound,lang)))

    def test_hash_and_duplicate_identity(self):
        records=self.samples('python'); records['b']=records['a']
        self.assertTrue(all(x['state']=='generated' for x in c.enumerate_candidates(records,'python')))
        records['a']=dict(records['a'],sha256='0'*64)
        with self.assertRaises(ValueError): c.enumerate_candidates(records,'python')

    def test_bad_fragments_and_whole_bodies(self):
        for lang in ('python','javascript'):
            pool=c.enumerate_candidates(self.samples(lang),lang)
            literals={x['literal'] for x in pool}
            self.assertTrue({' cons',' } els','214748364',' x','x '}.isdisjoint(literals))
            self.assertTrue(any(x['kind']=='function_opening' for x in pool))
            self.assertFalse(any(x['literal'].strip()==r['source'].strip() for x in pool for r in self.samples(lang).values()))
            src='def f(x):\n    x += 1\n' if lang=='python' else 'function f(x) { x += 1; }'
            self.assertFalse(any(x['kind']=='accumulator_update' for x in c.enumerate_candidates({'a':record(src)},lang)))

    def test_unicode_and_nested_headers(self):
        for lang,src,wanted in [('python','def f(xs):\n    é = "😀"\n    for x in xs[1:]:\n        é += x\n    return é\n','for x in xs[1:]:'),
            ('javascript','function f(xs) { const é="😀"; for (let i=0;i<xs.length;i++) { total += x; } return é; }','for (let i=0;i<xs.length;i++) {')]:
            pool=c.enumerate_candidates({'a':record(src)},lang)
            item=next(x for x in pool if x['kind']=='loop_opening' and x['literal']==wanted)
            self.assertEqual(item['literal'],wanted)
            p=item['provenance'][0]; self.assertEqual(src.encode()[p['start_byte']:p['end_byte']],wanted.encode())

    def test_python_lambda_header_and_nested_definition(self):
        source='def f():\n    while lambda: True:\n        def g():\n            pass\n        break\n    return 1\n'
        pool=c.enumerate_candidates({'a':record(source)},'python')
        self.assertEqual({x['literal'].strip() for x in pool if x['kind']=='loop_opening'},{'while lambda: True:'})

    def test_tables_and_no_escape(self):
        for lang in ('python','javascript'):
            records=self.samples(lang); pool=c.enumerate_candidates(records,lang)
            for width in (6,7,8):
                table=c.select_table(pool,lang,width)
                self.assertLessEqual(len(table['entries']),2**width)
                result=c.segment(records['a']['source'],table)
                self.assertFalse(result['complete']); self.assertIsNone(result['complete_program_bits'])
                self.assertGreater(result['uncovered_bytes'],0)
                self.assertEqual(result['selection_bits'],result['selections']*width)
            with self.assertRaises(ValueError): c.select_table(pool,lang,5)

    def test_complete_primitive_and_denominators(self):
        for lang in ('python','javascript'):
            records=self.samples(lang); pool=c.enumerate_candidates(records,lang)
            table=c.select_table(pool,lang,6)
            primitive='total += x' + (';' if lang=='javascript' else '')
            result=c.segment(primitive,table)
            self.assertTrue(result['complete']); self.assertEqual(result['complete_program_bits'],6)
            reports=c.evaluate_tables(records,lang,pool)
            self.assertEqual(set(reports),{6,7,8})
            self.assertTrue(all(r['total_programs']==2 and r['complete_programs']==0 for r in reports.values()))

    def test_broad_strict_full_programs(self):
        for lang in ('python','javascript'):
            records={}
            for a in (0,1):
                for b in (0,1):
                    source=(f'def solve(xs):\n    total = {a}\n    for x in xs:\n        total += x\n    return total + {b}\n'
                        if lang=='python' else
                        f'function solve(xs) {{ let total={a}; for (const x of xs) {{ total += x; }} return total + {b}; }}')
                    records[str((a,b))]=record(source)
            pool=c.enumerate_candidates(records,lang)
            self.assertTrue({'function_opening','declaration','return_statement'} <= {x['kind'] for x in pool})
            for report in c.evaluate_tables(records,lang,pool).values():
                self.assertEqual(report['complete_programs'],4)
                self.assertEqual(report['uncovered_bytes'],0)
                self.assertIn('complementary',report['table']['selection_method'])
                for key,result in report['programs'].items():
                    self.assertEqual(result['singleton_selections'],0)
                    decoded=''.join(report['table']['entries'][s['code']]['literal'] for s in result['spans'])
                    self.assertEqual(decoded,records[key]['source'])

    def test_javascript_else_comments_do_not_cut_tokens(self):
        source='function f(x) { if (x) { return 1; } else /* else */ { return 0; } }'
        pool=c.enumerate_candidates({'a':record(source)},'javascript')
        literals={x['literal'] for x in pool}
        self.assertIn('else /* else */ {',literals)
        self.assertNotIn('else */ {',literals)

    def test_frozen_table_validation_and_transfer(self):
        records=self.samples('javascript'); pool=c.enumerate_candidates(records,'javascript')
        table=c.select_table(pool,'javascript',6,records=records)
        before=copy.deepcopy(table)
        report=c.evaluate_fixed_table(records,table)
        self.assertFalse(report['selection_performed']); self.assertEqual(table,before)
        self.assertEqual(report['mapping_sha256'],table['mapping_sha256'])
        broken=copy.deepcopy(table); broken['entries'].append(broken['entries'][0])
        with self.assertRaises(ValueError): c.evaluate_fixed_table(records,broken)
        broken=copy.deepcopy(table); broken['mapping_sha256']='0'*64
        with self.assertRaises(ValueError): c.evaluate_fixed_table(records,broken)
        broken=copy.deepcopy(table); broken['entries'][0]['literal']='different'
        with self.assertRaises(ValueError): c.evaluate_fixed_table(records,broken)

    def test_segmentation_does_not_cut_comments(self):
        for lang,source in [('python','# total += x\ntotal += x'),('javascript','/* total += x; */ total += x;')]:
            pool=c.enumerate_candidates(self.samples(lang),lang)
            table=c.select_table(pool,lang,6)
            result=c.segment(source,table)
            self.assertGreater(result['uncovered_bytes'],0)
            comment_end=source.index('\n') if lang=='python' else source.index('*/')+2
            self.assertTrue(all(s['code'] is None or s['start_byte']>=comment_end for s in result['spans']))

    def test_constructor_transfer_without_full_statement_recurrence(self):
        for lang in ('python','javascript'):
            records={}
            for name in ('answer','result'):
                for operand in ('first','second'):
                    for number in ('10','20'):
                        source=(f'def solve(first, second):\n    {name} = {operand} + {number}\n    return {name}\n'
                            if lang=='python' else
                            f'function solve(first, second) {{ const {name} = {operand} + {number}; return {name}; }}')
                        records[source]=record(source)
            pool=c.enumerate_candidates(records,lang)
            eligible={x['literal'] for x in pool if x['state']=='promising'}
            self.assertIn('return ',eligible)
            self.assertIn('def solve(' if lang=='python' else 'function solve(',eligible)
            self.assertIn('first',eligible); self.assertIn('second',eligible)
            if lang=='javascript': self.assertIn('const ',eligible)
            table=c.select_table(pool,lang,8,records=records)
            # Frozen fitting has never contained this RHS, or its whole statement.
            changed=('def solve(first, second):\n    answer = first + second\n    return answer\n'
                if lang=='python' else
                'function solve(first, second) { const answer = first + second; return answer; }')
            self.assertNotIn('first + second',eligible)
            report=c.evaluate_fixed_table({'changed':record(changed)},table)
            self.assertEqual(report['complete_programs'],1)
            self.assertEqual(report['programs']['changed']['singleton_selections'],0)
            self.assertFalse(report['selection_performed'])
            self.assertTrue(all(c.promote(x)['state']!='trusted' for x in pool if x['kind']!='accumulator_update'))

    def test_constructor_boundaries_and_singleton_denial(self):
        samples=[('javascript','function solve(constant) { let value=2147483647; if (constant) { value++; } else { value--; } return value; }'),
            ('python','def solve(constant):\n    value = 2147483647\n    if constant:\n        value += 1\n    return value\n')]
        for lang,source in samples:
            pool=c.enumerate_candidates({'a':record(source)},lang)
            literals={x['literal'] for x in pool}
            self.assertIn('2147483647',literals)
            self.assertTrue({' cons',' } els','214748364',' x','x '}.isdisjoint(literals))
            parsed=c.metadata({'a':record(source)},lang)['a']; safe=c._safe_boundaries(source.encode(),parsed)
            for item in pool:
                for witness in item['provenance']:
                    self.assertIn(witness['start_byte'],safe); self.assertIn(witness['end_byte'],safe)
            table=c.select_table(pool,lang,8,states=('generated',))
            self.assertTrue(all(len(x['literal'].strip())>1 for x in table['entries']))

    def test_python_physical_lines_preserve_exact_spans(self):
        for separator in ('\u2028','\u2029','\x0b','\x0c','\x85'):
            for newline in ('\n','\r\n'):
                source=newline.join(['def f():',f'    value = "a{separator}b"','    total += value','    return total',''])
                records={'a':record(source)}
                pool=c.enumerate_candidates(records,'python')
                self.assertIn('total += value',{x['literal'] for x in pool})
                self.assertNotIn('\n    total += va',{x['literal'] for x in pool})
                shape=c.metadata(records,'python')['a']; safe=c._safe_boundaries(source.encode(),shape)
                for candidate in pool:
                    for witness in candidate['provenance']:
                        a,b=witness['start_byte'],witness['end_byte']
                        self.assertIn(a,safe); self.assertIn(b,safe)
                        self.assertEqual(source.encode()[a:b],candidate['literal'].encode())
        with self.assertRaises(ValueError):
            c.enumerate_candidates({'a':record('def f():\r    return 1\r')},'python')

    def test_cross_source_whole_body_contains_only_token_safe_units(self):
        for lang,first,second in [
            ('python','def f():\n    return total\n',
                'def g():\n    total = 1\n    return total;\n'),
            ('javascript','function f() { return total }',
                'function g() { let total=1; return total; }')]:
            records={'a':record(first),'b':record(second)}
            pool=c.enumerate_candidates(records,lang)
            self.assertFalse(any('return total' in x['literal'] for x in pool))
            third=('def h():\n    totals = "return total"\n    return totals\n' if lang=='python'
                else 'function h() { let totals="return total"; return totals; }')
            pool=c.enumerate_candidates({'a':record(first),'c':record(third)},lang)
            literals={x['literal'] for x in pool}
            self.assertIn('return totals' if lang=='python' else 'return totals;',literals)
            self.assertIn('"return total"',literals)

    def test_empty_frozen_audit_is_explicit_but_empty_fit_fails(self):
        records=self.samples('python')
        table=c.select_table(c.enumerate_candidates(records,'python'),'python',6)
        report=c.evaluate_fixed_table({},table)
        self.assertEqual(report['total_programs'],0); self.assertEqual(report['complete_programs'],0)
        self.assertEqual(report['programs'],{}); self.assertFalse(report['selection_performed'])
        broken=copy.deepcopy(table); broken['mapping_sha256']='0'*64
        with self.assertRaises(ValueError): c.evaluate_fixed_table({},broken)
        with self.assertRaises(ValueError): c.enumerate_candidates({},'python')

    def test_strict_glue_and_problem_identity(self):
        records=self.samples('python'); pool=c.enumerate_candidates(records,'python')
        strict=c.select_table(pool,'python',6)
        self.assertTrue(all(len(x['literal'].strip())>1 for x in strict['entries']))
        diagnostic=c.select_table(pool,'python',6,policy='charged_glue_diagnostic')
        self.assertTrue(any(len(x['literal'].strip())<=1 for x in diagnostic['entries']))
        result=c.segment(records['a']['source'],diagnostic)
        self.assertGreater(result['singleton_selections'],0)
        self.assertEqual(result['singleton_selection_bits'],result['singleton_selections']*6)
        records['b']['problem_id']=records['a']['problem_id']
        self.assertTrue(all(x['state']=='generated' for x in c.enumerate_candidates(records,'python')))

    def test_segment_refuses_partial_tokens(self):
        table={'language':'javascript','width':6,'stored_utf8_bytes':20,
               'entries':[{'literal':' cons'},{'literal':'214748364'},{'literal':' } els'}]}
        result=c.segment(' const value = 2147483647; if(value) { value++; } else { value--; }',table)
        self.assertEqual(result['selections'],0)

    def test_independent_verifier(self):
        for lang in ('python','javascript'):
            for literal in ('total += x','total -= x','a += b'):
                ev=verify_accumulator(literal,lang)
                self.assertTrue(ev['passed']); self.assertEqual(ev['cases'],289)
            for literal in ('a += a','obj.x += x','a += f()','a *= x','a += 1','a += x; evil()'):
                self.assertIsNone(verify_accumulator(literal,lang))


if __name__=='__main__': unittest.main()
