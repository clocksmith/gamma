"""Bounded authored primitive differentials, not native/corpus qualification."""
import json
from pathlib import Path
import random
import shutil
import subprocess
import tempfile
import unittest

from algsolve.synth import typed_vector_program as ir
from algsolve.synth import typed_word_javascript as javascript


def tagged(value):
    if type(value) is int:
        return {'integer': str(value)}
    if type(value) in (list, tuple):
        return [tagged(item) for item in value]
    return value


@unittest.skipUnless(shutil.which('node'), 'Node required for authored differentials')
class TypedWordJavaScriptPrimitiveTests(unittest.TestCase):
    def run_cases(self, cases, runner):
        # Imports below belong only to the test harness, never emitted support.
        harness = '''
const decode=x=>Array.isArray(x)?x.map(decode):x&&typeof x==='object'&&'integer'in x?BigInt(x.integer):x;
const encode=x=>typeof x==='bigint'?{integer:String(x)}:Array.isArray(x)?x.map(encode):x;
const cases=JSON.parse((await import('node:fs')).readFileSync(process.argv[2],'utf8'));
const capture=(f,budget)=>{try{return {value:encode(f()),remaining:String(budget.remaining)}}
 catch(e){return {error:e.name,message:e.message,remaining:String(budget.remaining)}}};
'''
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            script = root / 'run.mjs'
            script.write_text(javascript.RUNTIME.read_text(encoding='utf-8') + harness + runner, encoding='utf-8')
            inputs = root / 'cases.json'
            inputs.write_text(json.dumps(cases), encoding='utf-8')
            result = subprocess.run(['node', str(script), str(inputs)], text=True,
                                    capture_output=True, timeout=20)
            self.assertEqual(result.returncode, 0, result.stderr)
            return json.loads(result.stdout)

    @staticmethod
    def capture(function, budget):
        try:
            result = function()
            return {'value': tagged(result), 'remaining': str(budget.remaining)}
        except ir.Invalid as error:
            return {'error': type(error).__name__, 'message': str(error),
                    'remaining': str(budget.remaining)}

    def test_all_pure_operations_and_exact_internal_charges(self):
        rng = random.Random(17)
        cases = []
        for operation in ('add', 'sub', 'mul', 'eq', 'lt'):
            operands = [(0, 0), ((1 << 128) - 1, 1), (-((1 << 128) - 1), -1), (-11, 17)]
            operands += [(rng.randrange(-1000, 1000), rng.randrange(-1000, 1000)) for _ in range(30)]
            cases.extend((operation, list(pair)) for pair in operands)
        cases += [(operation, [a, b]) for operation in ('eq', 'lt')
                  for a in (False, True) for b in (False, True)]
        cases += [('not', [a]) for a in (False, True)]
        cases += [('neg', [a]) for a in (0, -((1 << 128) - 1), (1 << 128) - 1)]
        cases += [('tuple', [1, False, [2]]), ('field', [[1, False], 0]),
                  ('field', [[1, False], 1]), ('empty_ints', []), ('len', [[1, 2]])]
        cases += [('range', [n]) for n in (-1, 0, 1, 20000, 20001)]
        cases += [('append', [values, 4]) for values in ([], [1, 2], [1] * 19999, [1] * 20000)]
        cases += [('sort_by', [[[2, 10], [1, 11], [2, 12]], 0, reverse]) for reverse in (False, True)]
        requests, expected = [], []
        for operation, arguments in cases:
            for remaining in (1, 10, 1000000):
                budget = ir.Budget(remaining)

                def evaluate():
                    result = ir._pure(operation, arguments, budget)
                    # Python enforces this in _run, JavaScript in _twPure.
                    if type(result) is int:
                        ir.check_value(result, 'int')
                    return result

                expected.append(self.capture(evaluate, budget))
                requests.append({'operation': operation, 'arguments': tagged(arguments), 'budget': remaining})
        actual = self.run_cases(requests, '''
console.log(JSON.stringify(cases.map(r=>{const b=new _twBudget(r.budget);
 return capture(()=>_twPure(r.operation,decode(r.arguments),b),b)})));
''')
        for request, wanted, result in zip(requests, expected, actual):
            with self.subTest(operation=request['operation'], budget=request['budget']):
                self.assertEqual(result, wanted)
        self.assertEqual(len(actual), len(expected))

    def test_all_effects_budget_parity_and_failure_before_mutation(self):
        rng = random.Random(71)
        traces = []
        for kind in ('heap', 'queue', 'map', 'vector', 'dsu'):
            if kind in ('heap', 'queue'):
                calls = [('pop', [])] + [('push', [rng.randrange(-100, 100)]) for _ in range(90)]
                calls += [('pop', []) for _ in range(91)]
                if kind == 'queue':
                    calls.insert(40, ('size', []))
            elif kind == 'map':
                calls = [('has', [0]), ('get', [0, -1]), ('set', [0, (1 << 128) - 1]),
                         ('has', [0]), ('get', [0, 3]), ('set', [0, -((1 << 128) - 1)]), ('get', [0, 3])]
            elif kind == 'vector':
                calls = [('snapshot', [])] + [('append', [i]) for i in range(20)] + [('snapshot', [])]
            else:
                calls = [('union', [i, i + 1]) for i in range(19)]
                calls += [('find', [i]) for i in range(20)] + [('union', [0, 19]), ('find', [-1]), ('find', [20])]
            for budget in (1, 10, 1000000):
                traces.append({'kind': kind, 'budget': budget, 'calls': calls})
        # Recover the internal budget after a failed primitive so the next read
        # observes whether that failed call mutated the resource. This is test
        # instrumentation, not a capability exposed by compiled solve().
        traces += [
            {'kind': 'vector', 'budget': 1, 'calls': [('append', [3]), ('append', [4]), ('reset', [100]), ('snapshot', [])]},
            {'kind': 'heap', 'budget': 1, 'calls': [('push', [3]), ('push', [2]), ('pop', []), ('reset', [100]), ('pop', []), ('pop', [])]},
            {'kind': 'dsu', 'budget': 20, 'calls': [('union', [0, 1]), ('union', [2, 3]), ('union', [1, 3]), ('reset', [100]), ('find', [3])]},
        ]
        requests, expected = [], []
        for trace in traces:
            budget = ir.Budget(trace['budget'])
            try:
                resource = ir._effect(trace['kind'] + '.new', [20] if trace['kind'] == 'dsu' else [], budget)
            except ir.Invalid as error:
                expected.append([{'error': type(error).__name__, 'message': str(error), 'remaining': str(budget.remaining)}])
            else:
                results = []
                for operation, arguments in trace['calls']:
                    if operation == 'reset':
                        budget.remaining = arguments[0]
                        continue
                    results.append(self.capture(lambda: ir._effect(trace['kind'] + '.' + operation,
                                                                  [resource, *arguments], budget), budget))
                expected.append(results)
            requests.append({**trace, 'calls': [[operation, tagged(arguments)] for operation, arguments in trace['calls']]})
        actual = self.run_cases(requests, '''
console.log(JSON.stringify(cases.map(r=>{const b=new _twBudget(r.budget);let resource;
 const allocation=capture(()=>{resource=_twEffect(r.kind+'.new',r.kind==='dsu'?[20n]:[],b);return null},b);
 if(allocation.error)return [allocation];const results=[];
 for(const [op,args] of r.calls){if(op==='reset'){b.remaining=decode(args)[0];continue}
 results.push(capture(()=>_twEffect(r.kind+'.'+op,[resource,...decode(args)],b),b))}return results})));
''')
        for request, wanted, result in zip(requests, expected, actual):
            with self.subTest(kind=request['kind'], budget=request['budget']):
                self.assertEqual(result, wanted)
        self.assertEqual(len(actual), len(expected))


if __name__ == '__main__':
    unittest.main()
