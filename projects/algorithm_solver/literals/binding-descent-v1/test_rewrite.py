import json
import random
import subprocess
import unittest
import rewrite as r


class BindingDescentTests(unittest.TestCase):
    def record(self,text):return r.records({'x':text})['x']
    def colors(self,record):return [v['name'] for v in record['variables']]
    def variable(self,record,name):return next(v for v in record['variables'] if v['name']==name and v['eligible'])
    def result(self,text,args='3'):
        script="const vm=require('node:vm'),i=JSON.parse(require('node:fs').readFileSync(0,'utf8'));console.log(vm.runInNewContext(i.s+';JSON.stringify(solve('+i.a+'))',{},{timeout:1000}));"
        return subprocess.check_output(['node','-e',script],input=json.dumps({'s':text,'a':args}),text=True).strip()

    def test_disjoint_scope_names_can_share_letter(self):
        text='function solve(input){function f(left){return left+1}function g(right){return right*2}return f(input)+g(input)}'
        rec=self.record(text);self.assertFalse(rec['unsafe']);colors=self.colors(rec)
        for name in ('input','left','right'):colors[self.variable(rec,name)['id']]='a'
        self.assertTrue(r.legal(rec,colors));changed=r.render(text,rec,colors)
        self.assertEqual(self.result(changed),self.result(text))

    def test_enclosing_reference_conflicts_prevent_capture(self):
        text='function solve(outer){function f(inner){return outer+inner}return f(2)}'
        rec=self.record(text);colors=self.colors(rec);a=self.variable(rec,'outer');b=self.variable(rec,'inner')
        self.assertIn(b['id'],a['neighbors']);colors[a['id']]=colors[b['id']]='x'
        self.assertFalse(r.legal(rec,colors))

    def test_unresolved_name_cannot_be_shadowed(self):
        text='function solve(input){function f(local){return external+local}return f(input)}'
        rec=self.record(text);colors=self.colors(rec);v=self.variable(rec,'input');colors[v['id']]='external'
        self.assertIn('external',v['forbidden']);self.assertFalse(r.legal(rec,colors))

    def test_same_scope_conflict_even_for_unused_variables(self):
        rec=self.record('function solve(input){let unused=1;return input}')
        colors=self.colors(rec);colors[self.variable(rec,'input')['id']]=colors[self.variable(rec,'unused')['id']]='x'
        self.assertFalse(r.legal(rec,colors))

    def test_shorthand_and_inferred_name_bindings_reserved(self):
        rec=self.record('function solve(input){let held=input,arrow=()=>input;return {held,answer:arrow()}}')
        self.assertFalse(next(v for v in rec['variables'] if v['name']=='held')['eligible'])
        self.assertFalse(next(v for v in rec['variables'] if v['name']=='arrow')['eligible'])
        self.assertTrue(self.variable(rec,'input')['eligible'])

    def test_assignment_and_destructuring_inferred_function_names_reserved(self):
        text='function solve(input){let later;later=()=>input;let [fallback=()=>input]=[];return later()+fallback()}'
        rec=self.record(text)
        for name in ('later','fallback'):self.assertFalse(next(v for v in rec['variables'] if v['name']==name)['eligible'])
        self.assertTrue(self.variable(rec,'input')['eligible'])

    def test_property_spelling_preserved(self):
        text='function solve(value){let local=value;return {key:local}.key}'
        rec=self.record(text);colors=self.colors(rec);colors[self.variable(rec,'local')['id']]='k'
        changed=r.render(text,rec,colors);self.assertIn('{key:k}.key',changed)
        self.assertEqual(self.result(text),self.result(changed))

    def test_reflection_retains_original(self):
        text='function solve(input){return eval("input")}'
        rec=self.record(text);self.assertTrue(rec['unsafe'])
        changed,stats=r.optimize(text,rec,[chr(i) for i in range(32,127)]+['\n'])
        self.assertEqual(changed,text);self.assertEqual(stats['trials'],0)

    def test_many_valid_colorings_preserve_closure_and_mutation(self):
        text='function solve(input){let sum=0;function f(arg){sum+=arg;return input+sum}let out=[f(1),f(2)];for(let index=0;index<2;index++){let value=index;out.push(()=>value+sum)}return [out[0],out[1],out[2](),out[3]()]}'
        rec=self.record(text);self.assertFalse(rec['unsafe']);expected=self.result(text);rng=random.Random(7);valid=[]
        for _ in range(100):
            colors=self.colors(rec)
            for v in rec['variables']:
                if v['eligible']:
                    proposed=list(colors);proposed[v['id']]=rng.choice('abcdefg')
                    if r.legal(rec,proposed):colors=proposed
            valid.append(r.render(text,rec,colors))
        script="const vm=require('node:vm'),xs=JSON.parse(require('node:fs').readFileSync(0,'utf8'));console.log(JSON.stringify(xs.map(s=>vm.runInNewContext(s+';JSON.stringify(solve(3))',{},{timeout:1000}))));"
        got=json.loads(subprocess.check_output(['node','-e',script],input=json.dumps(valid),text=True))
        self.assertEqual(got,[expected]*100)

    def test_recursive_global_and_fixed_class_aliases_keep_eligible_locals(self):
        texts=['function solve(count){return count<1?0:1+solve(count-1)}',
            'function solve(input){class Box{constructor(value){this.value=value}get(){return this.value+input}}return new Box(input).get()}']
        for text in texts:
            rec=self.record(text);self.assertFalse(rec['unsafe']);colors=self.colors(rec)
            v=next(v for v in rec['variables'] if v['eligible']);colors[v['id']]='z'
            self.assertTrue(r.legal(rec,colors));self.assertEqual(self.result(text),self.result(r.render(text,rec,colors)))

    def test_trial_cap_keeps_a_complete_improving_source(self):
        text='function solve(longName){return longName+longName}'
        rec=self.record(text);vocab=[chr(i) for i in range(32,127)]+['\n']
        changed,stats=r.optimize(text,rec,vocab,max_trials=1)
        self.assertEqual(stats['stop'],'trial_limit');self.assertEqual(stats['trials'],1)
        self.assertLess(len(changed),len(text));self.assertEqual(self.result(text),self.result(changed))

    def test_scope_descent_beats_global_group_when_fixed_spelling_blocks(self):
        text='function solve(input){let same=input;function f(same){return same+1}return {same,answer:f(input)}}'
        rec=self.record(text);alphabet=[chr(i) for i in range(32,127)]+['\n']
        vocab=alphabet+['function f(a){return a+1}']
        global_text,g=r.optimize(text,rec,vocab,'global');scope_text,s=r.optimize(text,rec,vocab,'scope')
        tree=r.codec.trie(vocab)
        self.assertLess(len(r.codec.encode_text(scope_text,tree)),len(r.codec.encode_text(global_text,tree)))
        self.assertEqual(self.result(text),self.result(scope_text));self.assertGreater(s['moves'],0)


if __name__=='__main__':unittest.main()
