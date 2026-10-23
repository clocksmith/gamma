"""Generic synthetic scope/semantic checks; no research corpus access."""
import ast
import importlib.util
from pathlib import Path
import unittest
import tempfile
import graph

LIT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('python_binding_pure_optimizer', LIT/'binding-descent-v1/rewrite.py')
rewrite = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rewrite)


class GraphTests(unittest.TestCase):
    def changed(self, text, maps):
        r = graph.record(text)
        self.assertFalse(r['unsafe'], r)
        colors = [maps.get((v['scope'][1], v['name']), v['name']) for v in r['variables']]
        out = rewrite.render(text, r, colors)
        ast.parse(out)
        graph.validate_rewrite(text, out, r)
        return out

    def test_disjoint_scopes_reuse_same_target(self):
        text = 'def f(n):\n x=n+1\n return x\ndef g(n):\n y=n*2\n return y\n'
        out = self.changed(text, {('f','x'):'a', ('g','y'):'a'})
        ns={};exec(out,ns)
        self.assertEqual((ns['f'](4),ns['g'](4)),(5,8))

    def test_same_scope_collision_rejected(self):
        r = graph.record('def f(n):\n x=n+1\n y=n+2\n return x+y\n')
        self.assertFalse(rewrite.legal(r,['a']*len(r['variables'])))

    def test_parameters_and_keyword_interface_fixed(self):
        text = 'def f(n,*,step=2):\n result=n+step\n return result\n'
        out = self.changed(text,{('f','result'):'a'});ns={};exec(out,ns)
        self.assertEqual(ns['f'](n=4,step=3),7)
        self.assertEqual([v['name'] for v in graph.record(text)['variables']],['result'])

    def test_closure_capture_spelling_reserved(self):
        text = 'def f(n):\n captured=n\n spare=2\n def g():\n  local=3\n  return captured+local\n return spare+g()\n'
        r=graph.record(text)
        self.assertNotIn('captured',[v['name'] for v in r['variables']])
        out=self.changed(text,{('f','spare'):'a',('g','local'):'a'});ns={};exec(out,ns)
        self.assertEqual(ns['f'](4),9)

    def test_default_expression_uses_outer_binding(self):
        text='def f(n):\n value=n+1\n def g(arg=value):\n  extra=2\n  return arg+extra\n return g()\n'
        out=self.changed(text,{('f','value'):'a',('g','extra'):'b'});ns={};exec(out,ns)
        self.assertEqual(ns['f'](4),7)
        self.assertIn('arg=a',out)

    def test_comprehension_bindings_and_references_reserved(self):
        text='def f(n):\n values=[x+n for x in range(3)]\n result=sum(values)\n return result\n'
        r=graph.record(text)
        self.assertNotIn('x',[v['name'] for v in r['variables']])
        out=self.changed(text,{('f','values'):'a',('f','result'):'b'});ns={};exec(out,ns)
        self.assertEqual(ns['f'](2),9)

    def test_lambda_reference_reserved(self):
        text='def f(n):\n x=n\n op=lambda q:x+q\n result=op(2)\n return result\n'
        r=graph.record(text)
        self.assertNotIn('x',[v['name'] for v in r['variables']])
        out=self.changed(text,{('f','result'):'a'});ns={};exec(out,ns)
        self.assertEqual(ns['f'](3),5)

    def test_builtin_shadow_blocked(self):
        r=graph.record('def f(n):\n x=n\n return len([x])\n')
        self.assertFalse(rewrite.legal(r,['len']))

    def test_opaque_guards(self):
        for text in ('def f(n):return locals()', 'def f(n):return n.__code__',
                     'def f(n):return g(**n)', '@wrap\ndef f(n):return n',
                     'def f(é):return é'):
            self.assertTrue(graph.record(text)['unsafe'],text)

    def test_optimizer_generic_python_input(self):
        text='def f(n):\n value=n+1\n return value+value\n'
        vocab=[chr(i) for i in range(32,127)]+['\n','return a+a']
        out,stats=rewrite.optimize(text,graph.record(text),vocab,max_trials=6000)
        self.assertGreater(stats['moves'],0);graph.validate_rewrite(text,out,graph.record(text));ns={};exec(out,ns)
        self.assertEqual(ns['f'](4),10)

    def test_structural_audit_rejects_other_edits(self):
        text='def f(n):\n x=n+1\n return x+x\n'
        r=graph.record(text)
        for other in (text.replace('+1','+2'), text.replace('f(n)','f(q)').replace('=n','=q'),
                      text.replace('return x+x','return x-x'), text.replace('return x+x','return x+n')):
            with self.assertRaises(AssertionError):graph.validate_rewrite(text,other,r)

    def test_nonlocal_and_global_names_fixed(self):
        text='total=1\ndef f(n):\n held=n\n def g():\n  nonlocal held\n  global total\n  spare=2\n  held+=spare\n  return held+total\n return g()\n'
        r=graph.record(text)
        self.assertEqual([v['name'] for v in r['variables']],['spare'])
        out=self.changed(text,{('g','spare'):'a'});ns={};exec(out,ns)
        self.assertEqual(ns['f'](4),7)

    def test_comprehension_walrus_and_lambda_reserved(self):
        text='def f(n):\n last=0\n values=[(last:=x+n) for x in range(3)]\n result=last+sum(values)\n return result\n'
        self.assertNotIn('last',[v['name'] for v in graph.record(text)['variables']])
        out=self.changed(text,{('f','values'):'a',('f','result'):'b'});ns={};exec(out,ns)
        self.assertEqual(ns['f'](2),13)

    def test_nested_class_method_locals_remain_separate(self):
        text='def outer(n):\n class Inner:\n  def run(self,value):\n   temporary=value+1\n   return temporary\n answer=Inner().run(n)\n return answer\n'
        out=self.changed(text,{('run','temporary'):'a',('outer','answer'):'a'});ns={};exec(out,ns)
        self.assertEqual(ns['outer'](4),5)

    def test_class_private_spelling_fails_closed(self):
        text='class Box:\n def run(self,n):\n  __value=n+1\n  return __value\n'
        self.assertTrue(graph.record(text)['unsafe'])

    def test_annotations_are_preserved(self):
        text='def f(n:int)->int:\n result=n+1\n return result\n'
        out=self.changed(text,{('f','result'):'a'});ns={};exec(out,ns)
        self.assertEqual(ns['f'].__annotations__,{'n':int,'return':int})
        self.assertEqual(ns['f'](4),5)

    def optimize_observable(self,text):
        record=graph.record(text)
        vocab=[chr(i) for i in range(32,127)]+['\n','a=1','return a','a+=1']
        output,stats=rewrite.optimize(text,record,vocab,max_trials=6000)
        graph.validate_rewrite(text,output,record)
        before={};after={};exec(text,before);exec(output,after)
        return output,record,stats,before['solve'](),after['solve']()

    def test_debug_fstring_keeps_expression_name(self):
        text="def solve():\n value=1\n return f'{value=}'\n"
        out,r,stats,before,after=self.optimize_observable(text)
        self.assertNotIn('value',[v['name'] for v in r['variables']])
        self.assertEqual(out,text);self.assertEqual(stats['moves'],0)
        self.assertEqual(before,'value=1');self.assertEqual(after,before)

    def test_normal_fstring_conservatively_preserves_names(self):
        text="def solve():\n value=1\n return f'{value}'\n"
        out,r,stats,before,after=self.optimize_observable(text)
        self.assertNotIn('value',[v['name'] for v in r['variables']])
        self.assertEqual(out,text);self.assertEqual(stats['moves'],0)
        self.assertEqual(before,'1');self.assertEqual(after,before)

    @unittest.skipUnless(hasattr(ast,'TemplateStr'),'requires template-string AST')
    def test_template_string_expression_is_observable(self):
        text="def solve():\n value=1\n return t'{value}'\n"
        out,r,stats,before,after=self.optimize_observable(text)
        self.assertNotIn('value',[v['name'] for v in r['variables']])
        self.assertEqual(out,text);self.assertEqual(stats['moves'],0)
        self.assertEqual(before.interpolations[0].expression,'value')
        self.assertEqual(after.interpolations[0].expression,before.interpolations[0].expression)
        self.assertEqual(after.interpolations[0].value,before.interpolations[0].value)

    def test_caught_binding_errors_retain_entire_source(self):
        examples=[
            'def solve():\n try:\n  value+=1\n except Exception as error:\n  return str(error)\n',
            'def solve():\n result=""\n try:\n  value+=1\n except* Exception as error:\n  result=str(error.exceptions[0])\n return result\n',
        ]
        for text in examples:
            with self.subTest(text=text):
                out,r,stats,before,after=self.optimize_observable(text)
                self.assertTrue(r['unsafe']);self.assertEqual(r['reason'],'exception_handler_observability')
                self.assertEqual(out,text);self.assertEqual(stats['stop'],'unsupported')
                self.assertIn('value',before);self.assertEqual(before,after)

    def test_inspect_source_observation_retains_whole_source(self):
        texts=[
            'import inspect\ndef solve():\n value=1\n return inspect.getsource(solve)\n',
            'from inspect import getsource as source_text\ndef solve():\n value=1\n return source_text(solve)\n',
        ]
        vocab=[chr(i) for i in range(32,127)]+['\n','a=1']
        for index,text in enumerate(texts):
            with self.subTest(index=index),tempfile.TemporaryDirectory() as tmp:
                r=graph.record(text)
                self.assertTrue(r['unsafe']);self.assertIn(r['reason'],('reflection','reflection_import'))
                out,stats=rewrite.optimize(text,r,vocab,max_trials=6000)
                graph.validate_rewrite(text,out,r)
                self.assertEqual(out,text);self.assertEqual(stats['stop'],'unsupported')
                values=[]
                for which,source in [('before',text),('after',out)]:
                    path=Path(tmp)/(which+'.py');path.write_text(source)
                    spec=importlib.util.spec_from_file_location('source_guard_'+which,path)
                    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
                    values.append(module.solve())
                self.assertIn('value=1',values[0]);self.assertEqual(values[0],values[1])

    def test_source_and_stack_helper_aliases_are_unsupported(self):
        for name in ('getsource','getsourcelines','findsource','getframeinfo','getouterframes',
                     'getinnerframes','stack','trace','extract_stack','format_stack','getline'):
            self.assertTrue(graph.record('def solve():\n value=1\n return obj.'+name+'()\n')['unsafe'],name)
            self.assertTrue(graph.record('from helper import '+name+' as hidden\ndef solve():\n value=1\n return hidden()\n')['unsafe'],name)


class NewlineOffsetTests(unittest.TestCase):
    def test_python_newline_offsets_and_comment_controls(self):
        for newline in ('\n', '\r', '\r\n'):
            for separator in ('\x0b', '\x0c', '\x1c', '\x1d', '\x1e'):
                source = newline.join(('def solve(n):',
                    '    value = n + 1 # x' + separator + 'y',
                    '    doubled = value * 2', '    return doubled', ''))
                record = graph.record(source)
                self.assertFalse(record['unsafe'], (newline, repr(separator)))
                self.assertEqual({v['name'] for v in record['variables']}, {'value', 'doubled'})
                edits = [(a,b,'x' if v['name']=='value' else 'y')
                         for v in record['variables'] for a,b in v['spans']]
                changed = source
                for a,b,name in sorted(edits, reverse=True):
                    changed = changed[:a] + name + changed[b:]
                graph.validate_rewrite(source, changed, record)
                left, right = {}, {}
                exec(source, left); exec(changed, right)
                self.assertEqual(left['solve'](4), right['solve'](4))

if __name__=='__main__':unittest.main()
