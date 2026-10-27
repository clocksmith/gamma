"""Independent small state-model checks; no candidate or definition reads."""
import copy
from itertools import product
import unittest

from . import request_git_queue03_subset03_oracles as o


def wire(pid,init,steps):
    return [[o.CLASSES[pid]]+[op for op,_ in steps],[init]+[a for _,a in steps]]


class Queue03StateTests(unittest.TestCase):
    def test_examples_and_input_preservation(self):
        for pid,examples in o.EXAMPLES.items():
            for args,answer in examples:
                original=copy.deepcopy(args)
                self.assertEqual(o.expected(pid,args),answer)
                self.assertEqual(args,original)

    def test_encrypter_explicit_reverse_expansion(self):
        keys=list('abc')
        dictionary=['a','b','c','aa','ab','ac','ba','bb','bc','ca','cb','cc']
        for values in product(('aa','ab','bb'),repeat=3):
            for encrypted in ('aa','ab','bb','aaaa','aaab','aabb','bbaa','bbbb','zz'):
                options=[[k for k,v in zip(keys,values) if v==encrypted[i:i+2]] for i in range(0,len(encrypted),2)]
                possibilities={''.join(chars) for chars in product(*options)}
                answer=len(possibilities.intersection(dictionary))
                self.assertEqual(o.expected(2227,wire(2227,[keys,list(values),dictionary],[('decrypt',[encrypted])])),[None,answer])

    def test_atm_repeated_subtraction_greedy_independent(self):
        for counts in product((0,1),repeat=5):
            for amount in (1,20,30,50,60,100,120,200,300,500,550,600,700,870):
                inventory=list(counts)
                answers=[None,None]
                for _ in range(2):
                    left=amount
                    trial=inventory[:]
                    take=[0]*5
                    for i in range(4,-1,-1):
                        denomination=(20,50,100,200,500)[i]
                        while trial[i] and left>=denomination:
                            trial[i]-=1
                            left-=denomination
                            take[i]+=1
                    if left:
                        answers.append([-1])
                    else:
                        answers.append(take)
                        inventory=trial
                self.assertEqual(o.expected(2241,wire(2241,[],[('deposit',[list(counts)]),('withdraw',[amount]),('withdraw',[amount])])),answers)

    def test_interval_union_independent_merging(self):
        for pairs in product(((1,2),(2,4),(6,6)),repeat=4):
            intervals=[]
            steps=[]
            output=[None]
            for pair in pairs:
                intervals.append(pair)
                merged=[]
                for a,b in sorted(intervals):
                    if merged and a<=merged[-1][1]+1:
                        merged[-1][1]=max(merged[-1][1],b)
                    else:
                        merged.append([a,b])
                steps.extend((('add',list(pair)),('count',[])))
                output.extend((None,sum(b-a+1 for a,b in merged)))
            self.assertEqual(o.expected(2276,wire(2276,[],steps)),output)

    def test_seats_independent_row_prefix_model(self):
        for n,m in ((1,1),(2,3),(3,2)):
            actions=[('gather',[1,0]),('gather',[m,n-1]),('gather',[m+1,n-1]),('scatter',[1,n-1]),('scatter',[n*m,n-1])]
            for steps in product(actions,repeat=3):
                used=[0]*n
                outputs=[None]
                for op,(k,maxrow) in steps:
                    if op=='gather':
                        row=next((r for r in range(maxrow+1) if m-used[r]>=k),None)
                        answer=[] if row is None else [row,used[row]]
                        if row is not None:
                            used[row]+=k
                    else:
                        answer=sum(m-used[r] for r in range(maxrow+1))>=k
                        if answer:
                            for r in range(maxrow+1):
                                take=min(m-used[r],k)
                                used[r]+=take
                                k-=take
                    outputs.append(answer)
                self.assertEqual(o.expected(2286,wire(2286,[n,m],list(steps))),outputs)

    def test_editor_independent_two_stacks(self):
        actions=[('addText',['abc']),('deleteText',[2]),('cursorLeft',[1]),('cursorRight',[2]),('cursorLeft',[40])]
        for steps in product(actions,repeat=4):
            left,right=[],[]
            outputs=[None]
            for op,(value,) in steps:
                answer=None
                if op=='addText':
                    left.extend(value)
                elif op=='deleteText':
                    answer=min(value,len(left))
                    for _ in range(answer):
                        left.pop()
                elif op=='cursorLeft':
                    for _ in range(min(value,len(left))):
                        right.append(left.pop())
                    answer=''.join(left[-10:])
                else:
                    for _ in range(min(value,len(right))):
                        left.append(right.pop())
                    answer=''.join(left[-10:])
                outputs.append(answer)
            self.assertEqual(o.expected(2296,wire(2296,[],list(steps))),outputs)

    def test_infinite_set_complement_model(self):
        actions=[('popSmallest',[]),('addBack',[1]),('addBack',[2]),('addBack',[1000])]
        for steps in product(actions,repeat=5):
            missing=set()
            outputs=[None]
            for op,a in steps:
                answer=None
                if op=='addBack':
                    missing.discard(a[0])
                else:
                    answer=1
                    while answer in missing:
                        answer+=1
                    missing.add(answer)
                outputs.append(answer)
            self.assertEqual(o.expected(2336,wire(2336,[],list(steps))),outputs)

    def test_number_containers_reverse_history(self):
        actions=[('change',[1,1]),('change',[1,2]),('change',[2,1]),('find',[1]),('find',[2])]
        for steps in product(actions,repeat=4):
            history=[]
            outputs=[None]
            for op,a in steps:
                answer=None
                if op=='change':
                    history.append(tuple(a))
                else:
                    matches=[]
                    for index in {i for i,_ in history}:
                        latest=next(value for i,value in reversed(history) if i==index)
                        if latest==a[0]:
                            matches.append(index)
                    answer=min(matches,default=-1)
                outputs.append(answer)
            self.assertEqual(o.expected(2349,wire(2349,[],list(steps))),outputs)

    def test_food_pairwise_dominance_and_prefix_ties(self):
        foods=['a','aa','b']
        cuisines=['x','x','y']
        actions=[('changeRating',['a',1]),('changeRating',['aa',3]),('changeRating',['a',3]),('highestRated',['x']),('highestRated',['y'])]
        for initial in product((1,3),repeat=3):
            for steps in product(actions,repeat=3):
                ratings=list(initial)
                outputs=[None]
                for op,a in steps:
                    answer=None
                    if op=='changeRating':
                        ratings[foods.index(a[0])]=a[1]
                    else:
                        choices=[i for i,c in enumerate(cuisines) if c==a[0]]
                        for i in choices:
                            if all(ratings[i]>ratings[j] or (ratings[i]==ratings[j] and foods[i]<=foods[j]) for j in choices):
                                answer=foods[i]
                                break
                    outputs.append(answer)
                self.assertEqual(o.expected(2353,wire(2353,[foods,cuisines,list(initial)],list(steps))),outputs)

    def test_invalid_domains(self):
        bad=[(2227,[['a','a'],['aa','ab'],['a']],[]),(2227,[['a'],['a'],['a']],[]),
             (2227,[['a'],['aa'],['a']],[('encrypt',['z'])]),(2227,[['a'],['aa'],['a']],[('decrypt',['aaa'])]),
             (2241,[],[('deposit',[[0,0,0,0,0]])]),(2241,[],[('deposit',[[10**9,1,0,0,0]]),('withdraw',[1])]),
             (2241,[],[('deposit',[[0,0,0,0,0]]),('withdraw',[True])]),(2276,[],[('add',[1,2])]),
             (2276,[],[('add',[2,1]),('count',[])]),(2286,[1,1],[('gather',[1,1])]),(2286,[0,1],[]),
             (2296,[],[('addText',['A'])]),(2296,[],[('addText',['a'*41])]),(2296,[],[('deleteText',[0])]),
             (2336,[],[('addBack',[1001])]),(2349,[],[('change',[1,False])]),(2349,[],[('find',[0])]),
             (2353,[['a','a'],['x','x'],[1,1]],[]),(2353,[['a'],['x'],[1]],[('highestRated',['y'])]),
             (2353,[['a'],['x'],[1]],[('changeRating',['b',1])])]
        for pid,init,steps in bad:
            with self.subTest(pid=pid),self.assertRaises(ValueError):
                o.validate(pid,wire(pid,init,steps))
        for pid in o.IDS:
            valid=copy.deepcopy(o.EXAMPLES[pid][0][0])
            for malformed in (None,[],[[],[]],[[o.CLASSES[pid]],[]],valid+['extra']):
                with self.assertRaises(ValueError):
                    o.validate(pid,malformed)
            malformed=copy.deepcopy(valid)
            malformed[0][1]='unregisteredMethod'
            with self.assertRaises(ValueError):
                o.validate(pid,malformed)
            with self.assertRaises(ValueError):
                o.build_cases(pid,b'not pinned')

    def test_full_domain_not_reference_budget(self):
        probes={2227:wire(2227,[['a'],['aa'],['a'*100]],[('encrypt',['a'*2000])]*200),
                2241:wire(2241,[],[('deposit',[[10**9,0,0,0,0]])]+[('withdraw',[10**9])]*4999),
                2276:wire(2276,[],[('count',[])]*100000),
                2286:wire(2286,[50000,10**9],[('scatter',[10**9,49999])]*50000),
                2296:wire(2296,[],[('addText',['a'*40])]*20000),
                2336:wire(2336,[],[('popSmallest',[])]*1000),
                2349:wire(2349,[],[('find',[10**9])]*100000),
                2353:wire(2353,[['abcdefghij'],['klmnopqrst'],[10**8]],[('highestRated',['klmnopqrst'])]*20000)}
        for pid,args in probes.items():
            o.validate(pid,args)
            with self.assertRaises(ValueError):
                o.expected(pid,args)
            args[0].append(args[0][-1])
            args[1].append(args[1][-1])
            with self.assertRaises(ValueError):
                o.validate(pid,args)


if __name__=='__main__':
    unittest.main()
