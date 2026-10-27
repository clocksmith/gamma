"""Pure stdlib oracle checks; no candidate execution or definition file access."""
from itertools import product
import unittest
from . import request_git_queue02_subset03_oracles as o


class Queue02Tests(unittest.TestCase):
    def test_public_examples_independently_transcribed(self):
        for pid, args, answer in [(2110, [[3, 2, 1, 4]], 7), (2110, [[8, 6, 7, 7]], 4),
                                  (2110, [[1]], 1), (2221, [[1, 2, 3, 4, 5]], 8), (2221, [[5]], 5)]:
            self.assertEqual(o.expected(pid, args), answer)

    def test_small_brute_agrees_with_independent_large_reference(self):
        for pid, alphabet in [(2110, [1, 2, 3]), (2221, [0, 1, 9])]:
            for n in range(1, 7):
                for values in product(alphabet, repeat=n):
                    a = list(values)
                    self.assertEqual(o.expected(pid, [a]), o.analytic(pid, [a]))
                    self.assertEqual(a, list(values))

    def test_invalid_domain(self):
        for pid, args in [(2110, [[True]]), (2110, [[0]]), (2110, [[100001]]), (2110, [[1.0]]),
                          (2110, [[]]), (2221, [[10]]), (2221, [[-1]]), (2221, [[False]]),
                          (2221, [[1] * 1001]), (True, [[1]])]:
            with self.subTest(pid=pid, args=str(args)[:80]), self.assertRaises(ValueError):
                o.validate(pid, args)

    def test_full_domain_separate_from_reference_budget(self):
        o.validate(2110, [[1] * 100000])
        o.validate(2221, [[9] * 1000])
        self.assertEqual(o.analytic(2110, [list(range(100000, 0, -1))]), 5000050000)
        self.assertEqual(o.analytic(2221, [[9] * 1000]), (9 * pow(2, 999, 10)) % 10)
        for pid in (2110, 2221):
            with self.assertRaisesRegex(ValueError, 'budget'):
                o.expected(pid, [[1] * (o.SMALL_BUDGET[pid] + 1)])

    def test_definition_pin_fail_closed(self):
        with self.assertRaises(ValueError):
            o.public_examples(2110, b'not the official pinned response')

    def test_new_public_examples(self):
        examples = [(2117, [1, 4], '24e0'), (2117, [2, 11], '399168e2'), (2117, [371, 375], '7219856259e3'),
                    (2156, ['leetcode', 7, 20, 2, 0], 'ee'), (2156, ['fbxzaad', 31, 100, 3, 32], 'fbx'),
                    (2209, ['10110101', 2, 2], 2), (2209, ['11111', 2, 3], 0),
                    (2213, ['babacc', 'bcb', [1, 3, 3]], [3, 3, 4]), (2213, ['abyzz', 'aa', [2, 1]], [2, 3])]
        for pid, args, answer in examples:
            with self.subTest(pid=pid):
                self.assertEqual(o.expected(pid, args), answer)

    def test_product_independent_factorization(self):
        for left in range(1, 40):
            for right in range(left, 40):
                self.assertEqual(o.expected(2117, [left, right]), o.analytic(2117, [left, right]))
        self.assertEqual(o.expected(2117, [1, 10000]), o.analytic(2117, [1, 10000]))

    def test_hash_validator_independently_enumerated(self):
        for n in range(1, 6):
            for letters in product('az', repeat=n):
                s = ''.join(letters)
                for k in range(1, n+1):
                    for p, m in [(1, 1), (3, 5), (10**9, 999999937)]:
                        brute = [sum((ord(s[i+j])-96) * p**j for j in range(k)) % m for i in range(n-k+1)]
                        self.assertEqual(o._window_hashes(s, p, m, k), brute)
                        for h in set(brute):
                            self.assertEqual(o.expected(2156, [s,p,m,k,h]), s[brute.index(h):brute.index(h)+k])

    def test_carpet_independent_prefix_dynamic_reference(self):
        def dp(s, count, length):
            previous = [0]
            for ch in s:
                previous.append(previous[-1] + (ch == '1'))
            for _ in range(count):
                row = [0]
                for end, ch in enumerate(s, 1):
                    row.append(min(row[-1] + (ch == '1'), previous[max(0,end-length)]))
                previous = row
            return previous[-1]
        for n in range(1, 7):
            for bits in product('01', repeat=n):
                for count in range(1, 4):
                    for length in range(1, n+1):
                        s=''.join(bits)
                        self.assertEqual(o.expected(2209, [s,count,length]), dp(s,count,length))

    def test_repeating_substring_independent_intervals(self):
        for n in range(1, 5):
            for letters in product('ab', repeat=n):
                for index in range(n):
                    for char in 'ab':
                        changed=list(letters);changed[index]=char
                        result=max(j-i for i in range(n) for j in range(i+1,n+1) if len(set(changed[i:j])) == 1)
                        self.assertEqual(o.expected(2213, [''.join(letters),char,[index]]), [result])

    def test_new_domain_rejections(self):
        bad=[(2117,[True,3]),(2117,[4,3]),(2117,[1,10001]),(2156,['A',1,2,1,1]),
             (2156,['a',1,2,1,0]),(2156,['a',1,2,True,1]),(2209,['10',0,1]),
             (2209,['10',1,3]),(2209,['2',1,1]),(2213,['a','a',[True]]),
             (2213,['a','a',[1]]),(2213,['a','aa',[0]]),(2213,['a','','[]'])]
        for pid,args in bad:
            with self.subTest(pid=pid,args=args), self.assertRaises(ValueError):o.validate(pid,args)

    def test_structured_examples_and_no_host_mutation(self):
        import copy
        rows=[(2095, [[1,3,4,7,1,2,6]], [1,3,4,1,2,6]), (2095, [[1]], []),
              (2130, [[5,4,2,1]], 6), (2130, [[1,100000]], 100001),
              (2096, [[5,1,2,3,None,6,4],3,6], 'UURL'),
              (2080, [['RangeFreqQuery','query','query'], [[[12,33,4,56,22,2,34,33,22,12,34,56]],[1,2,4],[0,11,33]]], [None,1,2]),
              (2102, [['SORTracker','add','get','add','get'], [[],['b',2],[],['a',3],[]]], [None,None,'b',None,'b']),
              (2166, [['Bitset','fix','fix','flip','all','unfix','flip','one','unfix','count','toString'],[[5],[3],[1],[],[],[0],[],[],[0],[],[]]], [None,None,None,None,False,None,None,True,None,2,'01010'])]
        for pid,args,answer in rows:
            before=copy.deepcopy(args)
            self.assertEqual(o.expected(pid,args),answer)
            self.assertEqual(args,before)

    def test_linked_models_independent_index_relationships(self):
        for n in range(1,9):
            for values in product((1,9),repeat=n):
                a=list(values)
                self.assertEqual(o.expected(2095,[a]),a[:n//2]+a[n//2+1:])
                if n%2==0:
                    brute=max(a[i]+a[j] for i in range(n) for j in range(i+1,n) if i+j==n-1)
                    self.assertEqual(o.expected(2130,[a]),brute)

    def test_tree_bfs_against_root_path_difference(self):
        def paths(root):
            from collections import deque
            queue=deque([(root[0],'')]);result={root[0]:''};index=1
            while queue and index<len(root):
                parent,path=queue.popleft()
                for letter in 'LR':
                    if index==len(root):break
                    value=root[index];index+=1
                    if value is not None:result[value]=path+letter;queue.append((value,path+letter))
            return result
        for n in range(2,6):
            for shape in o._tree_shapes(n):
                root=o._shape_serialization(shape,iter(range(1,n+1)));positions=paths(root)
                for start in range(1,n+1):
                    for end in range(1,n+1):
                        if start==end:continue
                        a,b=positions[start],positions[end];same=0
                        while same<min(len(a),len(b)) and a[same]==b[same]:same+=1
                        self.assertEqual(o.expected(2096,[root,start,end]), 'U'*(len(a)-same)+b[same:])

    def test_frequency_traces_independent_positions(self):
        from bisect import bisect_left,bisect_right
        for n in range(1,7):
            for values in product((1,2),repeat=n):
                positions={v:[i for i,x in enumerate(values) if x==v] for v in (1,2,3)}
                queries=[[l,r,v] for l in range(n) for r in range(l,n) for v in (1,2,3)]
                args=[['RangeFreqQuery']+['query']*len(queries),[[list(values)]]+queries]
                expected=[None]+[bisect_right(positions[v],r)-bisect_left(positions[v],l) for l,r,v in queries]
                self.assertEqual(o.expected(2080,args),expected)

    def test_rank_trace_independent_ordinal_comparisons(self):
        for scores in product((1,2,3),repeat=5):
            names='edcba';locations=[];ordinal=0;answer=[None];ops=['SORTracker'];args=[[]]
            for name,score in zip(names,scores):
                locations.append((name,score));ops.extend(['add','get']);args.extend([[name,score],[]]);ordinal+=1
                winner=next(n for n,s in locations if sum(t>s or (t==s and m<n) for m,t in locations)==ordinal-1)
                answer.extend([None,winner])
            self.assertEqual(o.expected(2102,[ops,args]),answer)

    def test_bitset_boolean_model_against_integer_algebra(self):
        for size in range(1,4):
            actions=[('fix',[i]) for i in range(size)]+[('unfix',[i]) for i in range(size)]+[('flip',[])]
            for selected in product(actions,repeat=4):
                value=0;mask=(1<<size)-1
                for op,args in selected:
                    if op=='fix':value|=1<<args[0]
                    elif op=='unfix':value&=~(1<<args[0])
                    else:value^=mask
                ops=['Bitset']+[op for op,_ in selected]+['all','one','count','toString']
                args=[[size]]+[a for _,a in selected]+[[],[],[],[]]
                answer=[None]*5+[value==mask,bool(value),value.bit_count(),''.join(str((value>>i)&1) for i in range(size))]
                self.assertEqual(o.expected(2166,[ops,args]),answer)

    def test_structured_domain_rejections(self):
        bad=[(2095,[[]]),(2095,[[True]]),(2130,[[1]]),(2130,[[1,2,3]]),(2130,[[1,100001]]),
             (2096,[[1],1,1]),(2096,[[1,2,None],1,2]),(2096,[[1,None,None,2],1,2]),
             (2096,[[1,1],1,2]),(2096,[[1,3],1,3]),(2096,[[1,2],True,2]),
             (2080,[['RangeFreqQuery','query'],[[[1]],[0,0,True]]]),
             (2080,[['RangeFreqQuery','query'],[[[1]],[0,1,1]]]),
             (2102,[['SORTracker','get'],[[],[]]]),
             (2102,[['SORTracker','add','add'],[[],['a',1],['a',2]]]),
             (2166,[['Bitset','flip'],[[1],[]]]),(2166,[['Bitset','count'],[[True],[]]]),
             (2166,[['Bitset','fix','count'],[[1],[1],[]]]),
             (2166,[['Bitset']+['toString']*6,[[1]]+[[] for _ in range(6)]])]
        for pid,args in bad:
            with self.subTest(pid=pid,args=args),self.assertRaises(ValueError):o.validate(pid,args)

    def test_structured_full_domain_not_reference_budgets(self):
        o.validate(2095,[[100000]*100000]);o.validate(2130,[[1]*100000])
        o.validate(2080,[['RangeFreqQuery']+['query']*100000,[[[1]]]+[[0,0,1] for _ in range(100000)]])
        trace=[['Bitset']+['flip']*99999+['all'],[[100000]]+[[] for _ in range(100000)]]
        o.validate(2166,trace)
        with self.assertRaisesRegex(ValueError,'budget'):o.expected(2166,trace)


if __name__ == '__main__':
    unittest.main()
