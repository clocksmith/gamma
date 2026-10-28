"""Synthetic reference cross-checks only; no candidate import or execution."""
from collections import Counter, deque
from copy import deepcopy
from functools import lru_cache
from fractions import Fraction
from itertools import combinations, product
import json
import math
from pathlib import Path
import tempfile
import unittest

import cases
import oracles as o


class IndependentReferences(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=cases.build()

    def check(self,pid,reference):
        for row in self.data[pid]:
            self.assertTrue(o.matches(pid,row['args'],reference(*row['args']),row['expected']),
                            (pid,row['category'],str(row['args'])[:150]))

    def test_complete_population_and_unavailable_definitions_fail_closed(self):
        self.assertEqual(len(o.IDS),47);self.assertEqual(len(cases.IDS),40)
        self.assertEqual(set(o.IDS)-set(cases.IDS),set(o.BLOCKED_IDS))
        for pid in o.BLOCKED_IDS:
            with self.assertRaises(ValueError):o.expected(pid,[1])
        for pid in (True,553.0,'553',999999):
            with self.assertRaises(ValueError):o.validate_generated(pid,[[2]])

    def test_division_optimum_against_positive_integer_certificate(self):
        for row in self.data[553]:
            nums=row['args'][0];want=Fraction(nums[0],1)
            if len(nums)>1:want/=nums[1]
            for x in nums[2:]:want*=x
            value,leaves,_=o.parse_division(row['expected'])
            self.assertEqual(value,want);self.assertEqual(leaves,nums)
        for expression in ('(2)','2/(3)','2/((3/4))','3/(2/4)','2/3/4','2/(3/4)+1'):
            self.assertFalse(o.matches(553,[[2,3,4]],expression,'ignored'))
        self.assertFalse(o.matches(553,[[2,3]],'2/(3)','ignored'))
        self.assertTrue(o.matches(553,[[2,3,4]],'2/(3/4)','ignored'))

    def test_wall_explicit_crossings_against_frequency_of_internal_edges(self):
        def reference(wall):
            counts=Counter()
            for row in wall:
                pos=0
                for value in row[:-1]:pos+=value;counts[pos]+=1
            return len(wall)-max(counts.values(),default=0)
        self.check(554,reference)

    def test_digit_multisets_against_lexicographic_next_permutation(self):
        def reference(n):
            s=list(str(n));i=len(s)-2
            while i>=0 and s[i]>=s[i+1]:i-=1
            if i<0:return -1
            j=len(s)-1
            while s[j]<=s[i]:j-=1
            s[i],s[j]=s[j],s[i];s[i+1:]=reversed(s[i+1:]);v=int(''.join(s))
            return v if v<2**31 else -1
        self.check(556,reference)

    def test_interval_enumeration_against_prefix_frequency_counts(self):
        def reference(nums,k):
            seen=Counter({0:1});total=answer=0
            for n in nums:total+=n;answer+=seen[total-k];seen[total]+=1
            return answer
        self.check(560,reference)

    def test_orbits_against_disjoint_cycle_decomposition(self):
        def reference(nums):
            visited=set();best=0
            for start in range(len(nums)):
                if start in visited:continue
                v=start;length=0
                while v not in visited:visited.add(v);length+=1;v=nums[v]
                best=max(best,length)
            return best
        self.check(565,reference)

    def test_literal_windows_against_incremental_multiset(self):
        def reference(a,b):
            wanted=Counter(a);current=Counter(b[:len(a)])
            if current==wanted:return True
            for i in range(len(a),len(b)):
                current[b[i]]+=1;old=b[i-len(a)];current[old]-=1
                if not current[old]:del current[old]
                if current==wanted:return True
            return False
        self.check(567,reference)

    def test_forward_grid_paths_against_backwards_memoized_count(self):
        def reference(m,n,k,r,c):
            @lru_cache(None)
            def visit(k,r,c):
                if not 0<=r<m or not 0<=c<n:return 1
                if not k:return 0
                return sum(visit(k-1,rr,cc) for rr,cc in ((r+1,c),(r-1,c),(r,c+1),(r,c-1)))%o.MOD
            return visit(k,r,c)
        self.check(576,reference)

    def test_sorted_intervals_against_mismatch_endpoints(self):
        def reference(nums):
            positions=[i for i,(a,b) in enumerate(zip(nums,sorted(nums))) if a!=b]
            return positions[-1]-positions[0]+1 if positions else 0
        self.check(581,reference)

    def test_subsequence_sets_against_lcs_dynamic_program(self):
        def reference(a,b):
            row=[0]*(len(b)+1)
            for c in a:
                new=[0]
                for j,d in enumerate(b):new.append(row[j]+1 if c==d else max(new[-1],row[j+1]))
                row=new
            return len(a)+len(b)-2*row[-1]
        self.check(583,reference)

    def test_fraction_library_against_unreduced_common_denominator(self):
        def reference(expression):
            values=[tuple(map(int,t.split('/'))) for t in o.re.findall(r'[+-]?[0-9]+/[0-9]+',expression)]
            denominator=math.prod(d for _,d in values);numerator=sum(n*(denominator//d) for n,d in values);gcd=math.gcd(numerator,denominator)
            return str(numerator//gcd)+'/'+str(denominator//gcd)
        self.check(592,reference)

    def test_square_orderings_against_pairwise_distances(self):
        def reference(*points):
            d=sorted((a[0]-b[0])**2+(a[1]-b[1])**2 for a,b in combinations(points,2))
            return d[0]>0 and d[:4]==[d[0]]*4 and d[4:]==[2*d[0]]*2
        self.check(593,reference)

    def test_explicit_matrix_against_common_incremented_rectangle(self):
        self.check(598,lambda m,n,ops:min([m]+[a for a,b in ops])*min([n]+[b for a,b in ops]))

    def test_duplicate_file_groups_have_exact_membership_and_multiplicity(self):
        for row in self.data[609]:
            args=row['args'];want=row['expected']
            self.assertTrue(o.matches(609,args,[list(reversed(g)) for g in reversed(want)],want))
            if want:self.assertFalse(o.matches(609,args,want+want[:1],want))
        self.assertFalse(o.matches(609,[],[['one']],[]))

    def test_triangle_triples_against_sorted_two_pointer_count(self):
        def reference(nums):
            a=sorted(nums);answer=0
            for k in range(2,len(a)):
                i,j=0,k-1
                while i<j:
                    if a[i]+a[j]>a[k]:answer+=j-i;j-=1
                    else:i+=1
            return answer
        self.check(611,reference)

    def test_scheduling_states_against_idle_lower_bound_certificate(self):
        def reference(tasks,gap):
            counts=Counter(tasks);most=max(counts.values());ties=sum(c==most for c in counts.values())
            return max(len(tasks),(most-1)*(gap+1)+ties)
        self.check(621,reference)

    def test_cross_array_pairs_against_extreme_value_scan(self):
        def reference(arrays):
            low,high=arrays[0][0],arrays[0][-1];best=0
            for a in arrays[1:]:best=max(best,abs(a[-1]-low),abs(high-a[0]));low=min(low,a[0]);high=max(high,a[-1])
            return best
        self.check(624,reference)

    def test_square_complements_against_monotonic_two_pointer_search(self):
        def reference(c):
            a,b=0,math.isqrt(c)
            while a<=b:
                total=a*a+b*b
                if total==c:return True
                if total<c:a+=1
                else:b-=1
            return False
        self.check(633,reference)

    def test_exclusive_interval_partition_against_event_stack_durations(self):
        def reference(n,logs):
            out=[0]*n;stack=[];last=0
            for raw in logs:
                ident,kind,t=raw.split(':');ident=int(ident);t=int(t)
                if kind=='start':
                    if stack:out[stack[-1]]+=t-last
                    stack.append(ident);last=t
                else:out[stack.pop()]+=t-last+1;last=t+1
            return out
        self.check(636,reference)

    def test_quantity_shortest_paths_against_remaining_need_recursion(self):
        def reference(price,offers,needs):
            @lru_cache(None)
            def visit(left):
                best=sum(a*b for a,b in zip(left,price))
                for offer in offers:
                    if all(a<=b for a,b in zip(offer,left)):
                        nxt=tuple(b-a for a,b in zip(offer,left));best=min(best,offer[-1]+visit(nxt))
                return best
            return visit(tuple(needs))
        self.check(638,reference)

    def test_equations_by_direct_substitution(self):
        for row in self.data[640]:
            equation=row['args'][0];answer=row['expected'];left,right=map(o.equation_terms,equation.split('='))
            if answer.startswith('x='):
                value=int(answer[2:]);self.assertEqual(left[0]*value+left[1],right[0]*value+right[1]);self.assertNotEqual(left[0],right[0])
            elif answer=='Infinite solutions':self.assertEqual(left,right)
            else:self.assertEqual(left[0],right[0]);self.assertNotEqual(left[1],right[1])

    def test_chain_subsets_against_greedy_finishing_order(self):
        def reference(pairs):
            end=-math.inf;count=0
            for a,b in sorted(pairs,key=lambda p:p[1]):
                if a>end:count+=1;end=b
            return count
        self.check(646,reference)

    def test_palindrome_substrings_against_center_expansion(self):
        def reference(s):
            answer=0
            for center in range(2*len(s)-1):
                a,b=center//2,(center+1)//2
                while a>=0 and b<len(s) and s[a]==s[b]:answer+=1;a-=1;b+=1
            return answer
        self.check(647,reference)

    def test_root_scan_against_prefix_trie(self):
        def reference(dictionary,sentence):
            trie={}
            for word in dictionary:
                node=trie
                for c in word:node=node.setdefault(c,{})
                node['']=True
            def replace(word):
                node=trie
                for i,c in enumerate(word):
                    if c not in node:return word
                    node=node[c]
                    if '' in node:return word[:i+1]
                return word
            return ' '.join(map(replace,sentence.split()))
        self.check(648,reference)

    def test_optimal_ban_tree_against_earliest_opponent_queue(self):
        def reference(s):
            r=deque(i for i,c in enumerate(s) if c=='R');d=deque(i for i,c in enumerate(s) if c=='D')
            while r and d:
                a,b=r.popleft(),d.popleft()
                if a<b:r.append(a+len(s))
                else:d.append(b+len(s))
            return 'Radiant' if r else 'Dire'
        self.check(649,reference)

    def test_copy_paste_reachability_against_prime_factor_certificate(self):
        def reference(n):
            total=0;factor=2
            while factor*factor<=n:
                while n%factor==0:total+=factor;n//=factor
                factor+=1
            return total+(n if n>1 else 0)
        self.check(650,reference)

    def test_closest_selection_checks_full_tie_order(self):
        self.assertEqual(o.expected(658,[[1,2,3,4],2,2]),[1,2])
        self.assertEqual(o.expected(658,[[1,1,2,3],3,0]),[1,1,2])

    def test_multiset_cover_against_consecutive_tail_extension(self):
        def reference(nums):
            count=Counter(nums);ends=Counter()
            for n in nums:
                if not count[n]:continue
                count[n]-=1
                if ends[n-1]:ends[n-1]-=1;ends[n]+=1
                elif count[n+1] and count[n+2]:count[n+1]-=1;count[n+2]-=1;ends[n+2]+=1
                else:return False
            return True
        self.check(659,reference)

    def test_one_removed_index_against_local_repair_copy(self):
        def reference(nums):
            a=nums[:];changed=0
            for i in range(1,len(a)):
                if a[i]>=a[i-1]:continue
                changed+=1
                if changed>1:return False
                if i<2 or a[i]>=a[i-2]:a[i-1]=a[i]
                else:a[i]=a[i-1]
            return True
        self.check(665,reference)

    def test_multiplication_table_answers_have_correct_rank(self):
        for row in self.data[668]:
            m,n,k=row['args'];v=row['expected']
            self.assertLess(sum(min(n,(v-1)//i) for i in range(1,m+1)),k)
            self.assertGreaterEqual(sum(min(n,v//i) for i in range(1,m+1)),k)

    def test_all_swaps_against_rightmost_larger_digit(self):
        def reference(n):
            digits=list(str(n));last={c:i for i,c in enumerate(digits)}
            for i,c in enumerate(digits):
                for d in '9876543210':
                    if d>c and last.get(d,-1)>i:
                        j=last[d];digits[i],digits[j]=digits[j],digits[i];return int(''.join(digits))
            return n
        self.check(670,reference)

    def test_button_parities_against_literal_exact_press_reachability(self):
        for n in range(1,9):
            states={(1<<n)-1};buttons=[sum(1<<(i-1) for i in range(1,n+1) if condition(i)) for condition in (lambda i:True,lambda i:i%2==0,lambda i:i%2==1,lambda i:i%3==1)]
            for presses in range(9):
                self.assertEqual(o.expected(672,[n,presses]),len(states));states={s^b for s in states for b in buttons}

    def test_lis_subsets_against_length_count_dp(self):
        def reference(nums):
            length=[1]*len(nums);count=[1]*len(nums)
            for j in range(len(nums)):
                for i in range(j):
                    if nums[i]<nums[j]:
                        if length[i]+1>length[j]:length[j]=length[i]+1;count[j]=count[i]
                        elif length[i]+1==length[j]:count[j]+=count[i]
            return sum(c for c,l in zip(count,length) if l==max(length))
        self.check(673,reference)

    def test_wildcard_balances_against_lower_upper_bounds(self):
        def reference(s):
            low=high=0
            for c in s:
                low=max(0,low+(1 if c=='(' else -1));high+=-1 if c==')' else 1
                if high<0:return False
            return low==0
        self.check(678,reference)

    def test_literal_deletions_against_first_mismatch_split(self):
        def reference(s):
            i,j=0,len(s)-1
            while i<j and s[i]==s[j]:i+=1;j-=1
            return s[i+1:j+1]==s[i+1:j+1][::-1] or s[i:j]==s[i:j][::-1]
        self.check(680,reference)

    def test_edge_removal_against_online_disjoint_sets(self):
        def reference(edges):
            parent=list(range(len(edges)+1));answer=None
            def find(v):
                while parent[v]!=v:parent[v]=parent[parent[v]];v=parent[v]
                return v
            for a,b in edges:
                aa,bb=find(a),find(b)
                if aa==bb:answer=[a,b]
                else:parent[aa]=bb
            return answer
        self.check(684,reference)

    def test_repeated_string_cross_boundary_controls(self):
        for a,b,want in [('abcd','cdabcdab',3),('abc','cabcabca',4),('a','aa',2),('ab','baab',-1)]:
            self.assertEqual(o.expected(686,[a,b]),want)

    def test_integer_knight_counts_against_probability_recursion(self):
        moves=[(a,b) for a in (-2,-1,1,2) for b in (-2,-1,1,2) if abs(a)+abs(b)==3]
        def reference(n,k,r,c):
            @lru_cache(None)
            def visit(k,r,c):
                if not 0<=r<n or not 0<=c<n:return 0.0
                if k==0:return 1.0
                return sum(visit(k-1,r+a,c+b) for a,b in moves)/8
            return visit(k,r,c)
        self.check(688,reference)
        self.assertFalse(o.matches(688,[],True,1.0));self.assertFalse(o.matches(688,[],math.nan,1.0))

    def test_word_ordering_uses_frequency_then_lexicographic_tie(self):
        self.assertEqual(o.expected(692,[['b','b','a','a','c'],2]),['a','b'])

    def test_land_components_against_union_find_areas(self):
        def reference(grid):
            rows=len(grid);cols=len(grid[0]);parent=list(range(rows*cols));size=[1]*(rows*cols)
            def find(v):
                while v!=parent[v]:parent[v]=parent[parent[v]];v=parent[v]
                return v
            for r in range(rows):
                for c in range(cols):
                    if not grid[r][c]:continue
                    for rr,cc in ((r-1,c),(r,c-1)):
                        if rr>=0 and cc>=0 and grid[rr][cc]:
                            a,b=find(r*cols+c),find(rr*cols+cc)
                            if a!=b:parent[a]=b;size[b]+=size[a]
            return max([0]+[size[find(r*cols+c)] for r in range(rows) for c in range(cols) if grid[r][c]])
        self.check(695,reference)

    def test_partition_cover_against_bucket_assignment(self):
        def reference(nums,k):
            total=sum(nums)
            if total%k:return False
            target=total//k;values=sorted(nums,reverse=True);buckets=[0]*k
            def assign(i):
                if i==len(values):return len(set(buckets))==1
                tried=set()
                for j in range(k):
                    if buckets[j] in tried or buckets[j]+values[i]>target:continue
                    tried.add(buckets[j]);buckets[j]+=values[i]
                    if assign(i+1):return True
                    buckets[j]-=values[i]
                return False
            return assign(0)
        self.check(698,reference)

    def test_reference_budgets_are_separate_from_input_domain(self):
        for pid,args in [(560,[[1]*201,1]),(565,[list(range(501))]),(583,['a'*16,'b']),
                         (621,[['A']*13,1]),(649,['R'*13]),(668,[30000,30000,1]),
                         (673,[[1]*19]),(680,['a'*501]),(698,[list(range(1,17)),8])]:
            o.validate_generated(pid,args)
            with self.assertRaises(ValueError):o.expected(pid,args)

    def test_exact_domains_and_structure_rejections(self):
        invalid={553:[[[1]],[[True]],[[2]*11]],556:[[True],[0],[2**31]],
                 565:[[[1,1]],[[0,2]]],576:[[0,1,0,0,0],[1,1,0,1,0]],
                 592:[['1/0'],['2/4'],['1/2+']],593:[[[0,0]]*3],
                 636:[[1,['0:start:0','0:end:0','0:start:0','0:end:1']]],
                 638:[[[1],[[0,0]],[1]]],640:[['2x=1'],['01x=x']],
                 658:[[[2,1],1,0]],672:[[0,1],[1,-1]],
                 684:[[[1,2],[2,3],[1,2]]],688:[[1,0,1,0]],698:[[[1]*5,1]]}
        for pid,rows in invalid.items():
            for args in rows:
                with self.subTest(pid=pid,args=args),self.assertRaises(ValueError):o.validate_generated(pid,args)

    def test_references_preserve_arguments_and_observer_effects_fail_closed(self):
        for pid in cases.IDS:
            row=self.data[pid][0];before=deepcopy(row['args']);o.expected(pid,row['args']);self.assertEqual(row['args'],before)
        args=[[1,1],2];want=1;record={'result':want,'result_type':'int','args_before':deepcopy(args),'args_after':deepcopy(args),'alias_edges':[]}
        self.assertEqual(o.compare(560,args,want,record,'python'),(True,None))
        for changed,reason in [({'result':True},'result_value'),({'result_type':'bool'},'result_type'),({'args_after':[[2,1],2]},'input_effects'),({'alias_edges':[['result','args.0']]},'mutable_return_alias'),({'error':'retained'},'candidate_error')]:
            self.assertEqual(o.compare(560,args,want,dict(record,**changed),'python'),(False,reason))

    def test_official_example_parser_uses_independent_literal_values(self):
        value={'data':{'question':{'questionFrontendId':'560','content':'<pre><strong>Input:</strong> nums = [1,1], k = 2\n<strong>Output:</strong> 1\n<strong>Explanation:</strong> public example</pre>'}}}
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'560.json';p.write_text(json.dumps(value));self.assertEqual(cases.official_examples(p),[([[1,1],2],1)])

    def test_packet_plan_preserves_caps_coverage_and_first_call_repetition(self):
        repaired=[]
        for pid,values in self.data.items():
            groups=cases.batch_plan(values)
            self.assertEqual(set(i for group in groups for i in group),set(range(len(values))))
            for indices in groups:
                self.assertGreaterEqual(len(indices),2);self.assertEqual(indices[0],indices[-1])
                wire=cases.encoded(cases.packet(values,indices));self.assertLessEqual(len(wire),cases.MAX_HOST_PACKET_BYTES)
                self.assertLessEqual(cases.projected_output_bytes(values,indices),cases.MAX_EXPECTED_OUTPUT_BYTES)
                value=cases.packet(values,indices)
                self.assertEqual(set(value),{'entry','calls'})
                self.assertTrue(all(set(c)=={'args'} for c in value['calls']))
                if len(indices)==3 and values[indices[1]].get('isolate') and indices[0]!=indices[1]:repaired.append(pid)
        self.assertEqual(repaired,[])
        # Existing RLIMIT_FSIZE applies to child writes, not host-created inputs.
        self.assertTrue(any(len(cases.encoded(cases.packet(values,group)))>1024**2
                            for values in self.data.values() for group in cases.batch_plan(values)))
        synthetic=[{'args':[0],'expected':0},
                   {'args':['x'*(5*1024**2)],'expected':0,'isolate':True}]
        plan=cases.batch_plan(synthetic);self.assertEqual(plan,[[0,0],[0,1,0]])
        with self.assertRaises(ValueError):cases.batch_plan([{'args':['x'*cases.MAX_HOST_PACKET_BYTES],'expected':0}])


if __name__=='__main__':unittest.main()
