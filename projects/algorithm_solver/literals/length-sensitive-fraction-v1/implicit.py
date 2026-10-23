"""Synthetic-only length-binned full-substring dual. No corpus loader/runner."""
from __future__ import annotations

import bisect
import heapq
import importlib.util
from pathlib import Path
import os
import sys

_spec=importlib.util.spec_from_file_location('length_sensitive_parent_index',Path(__file__).resolve().parents[1]/'all-substring-fraction-v1/implicit.py')
parent=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(parent)
BINS=((1,1),(2,2),(3,3),(4,4),(5,8),(9,16),(17,32),(33,64),(65,128),(129,256),(257,None))


def require_checks():
    if not __debug__ or sys.flags.optimize or 'PYTHONOPTIMIZE' in os.environ:
        raise RuntimeError('Optimized Python/PYTHONOPTIMIZE forbidden for certificate checks')


def bin_index(length):
    assert type(length) is int and length>=1
    return next(b for b,(lo,hi) in enumerate(BINS) if lo<=length and (hi is None or length<=hi))


def validate_q(texts,q,capacity,denominator):
    require_checks()
    assert type(capacity) is int and capacity>=0
    assert type(denominator) is int and denominator>0
    assert set(q)==set(texts)
    for pid,text in texts.items():
        assert len(q[pid])==len(text)
        assert all(len(row)==len(BINS) and all(type(x) is int and x>=0 for x in row) for row in q[pid])


def lift_start_multipliers(q):
    """Embed item33 exactly; this is a feasible diagnostic, not an optimizer."""
    return {pid:[[value]*len(BINS) for value in values] for pid,values in q.items()}


class MinimumTree:
    """Production online minimum of (integer cost, endpoint), half-open queries."""
    def __init__(self,length):
        self.n=1
        while self.n<length:self.n*=2
        self.data=[None]*(2*self.n)

    @staticmethod
    def minimum(a,b):
        return b if a is None else a if b is None else min(a,b)

    def set(self,at,value):
        at+=self.n;self.data[at]=value
        while at>1:
            at//=2;self.data[at]=self.minimum(self.data[2*at],self.data[2*at+1])

    def query(self,left,right):
        left+=self.n;right+=self.n;answer=None
        while left<right:
            if left&1:answer=self.minimum(answer,self.data[left]);left+=1
            if right&1:right-=1;answer=self.minimum(answer,self.data[right])
            left//=2;right//=2
        return answer


def interval_minimum(tree,left,right,blocked):
    """Inclusive endpoint interval, excluding exact ban endpoints only."""
    if left>right:return None
    answer=None;cursor=left
    first=bisect.bisect_left(blocked,left);last=bisect.bisect_right(blocked,right)
    for end in blocked[first:last]:
        answer=tree.minimum(answer,tree.query(cursor,end));cursor=end+1
    return tree.minimum(answer,tree.query(cursor,right+1))


class Index:
    def __init__(self,texts,banned):
        require_checks();self.base=parent.Index(texts,banned);self.texts=self.base.texts
        self.pieces=[]
        for gid,g in enumerate(self.base.groups):
            for b,(low,high) in enumerate(BINS):
                first=max(low,g['first']);last=min(high if high is not None else g['last'],g['last'])
                if first>last:continue
                excluded=[length for length in g['excluded_lengths'] if first<=length<=last]
                self.pieces.append({'group':gid,'bin':b,'lo':g['lo'],'hi':g['hi'],'first':first,'last':last,
                                    'excluded_lengths':excluded,'multiplicity':last-first+1-len(excluded)})
        self.by_bin=[[] for _ in BINS]
        for k,p in enumerate(self.pieces):self.by_bin[p['bin']].append(k)
        self.distinct_allowed_entries=sum(p['multiplicity'] for p in self.pieces)
        assert self.distinct_allowed_entries==self.base.distinct_allowed_entries

    def weighted_selection(self,q,capacity):
        weights=[0]*len(self.pieces)
        for b in range(len(BINS)):
            prefix=[0]
            for pid,start in self.base.positions:prefix.append(prefix[-1]+q[pid][start][b])
            for k in self.by_bin[b]:
                p=self.pieces[k];weights[k]=prefix[p['hi']]-prefix[p['lo']]
        left=capacity;selected=[];total=0
        for k in sorted(range(len(self.pieces)),key=lambda k:(-weights[k],k)):
            count=min(left,self.pieces[k]['multiplicity'])
            if count:selected.append((k,count));total+=weights[k]*count;left-=count
            if left==0:break
        return total,selected

    def selected_occurrences(self,selected):
        """Dictionary term derivative by (source,start,bin), no word expansion."""
        result={pid:[[0]*len(BINS) for _ in text] for pid,text in self.texts.items()}
        for b in range(len(BINS)):
            difference=[0]*(len(self.base.positions)+1)
            for k,count in selected:
                p=self.pieces[k]
                if p['bin']==b:difference[p['lo']]+=count;difference[p['hi']]-=count
            active=0
            for rank,(pid,start) in enumerate(self.base.positions):
                active+=difference[rank];result[pid][start][b]=active
        return result

    def selected_vocabulary(self,selected,longest_first=False):
        """Materialize at most capacity words for a separately audited witness."""
        words=[]
        for k,count in selected:
            p=self.pieces[k];assert 0<count<=p['multiplicity'];pid,start=self.base.positions[p['lo']]
            blocked=set(p['excluded_lengths'])
            lengths=range(p['last'],p['first']-1,-1) if longest_first else range(p['first'],p['last']+1)
            for length in lengths:
                if length in blocked:continue
                words.append(self.texts[pid][start:start+length]);count-=1
                if count==0:break
            assert count==0
        return words

    def certificate(self,q,capacity=256,denominator=1000000):
        validate_q(self.texts,q,capacity,denominator)
        path_numerators={};path_starts={}
        for pid,text in sorted(self.texts.items()):
            n=len(text);tree=MinimumTree(n+1);tree.set(n,(0,n));cost=[None]*n+[0];back=[None]*n
            for start in range(n-1,-1,-1):
                blocked=sorted(self.base.banned_ends[pid][start]);choices=[]
                for b,(low,high) in enumerate(BINS):
                    left=start+low;right=min(n,start+high) if high is not None else n
                    best=interval_minimum(tree,left,right,blocked)
                    if best is not None:
                        value,end=best;choices.append((value+q[pid][start][b]+(9 if b==0 else -1)*denominator,end,b))
                if choices:
                    value,end,b=min(choices);cost[start]=value;back[start]=(end,b);tree.set(start,(value,start))
            if cost[0] is None:raise ValueError('full allowed pool cannot cover a source')
            path_numerators[pid]=cost[0];used=[[0]*len(BINS) for _ in text];at=0
            while at<n:
                end,b=back[at];used[at][b]=1;at=end
            path_starts[pid]=used
        top,selected=self.weighted_selection(q,capacity);numerator=sum(path_numerators.values())-top
        return {'numerator':numerator,'denominator':denominator,'integer_lower_bound':-(-numerator//denominator),
                'path_numerators':path_numerators,'top_capacity_numerator':top,'selected_pieces':selected,'path_starts':path_starts}


def independently_relocate_bans(base):
    """Independent sliced-prefix searches; no cached production endpoint sets."""
    ends={pid:[set() for _ in text] for pid,text in base.texts.items()}
    for word in base.banned:
        bounds=[]
        for after in (False,True):
            left,right=0,len(base.positions)
            while left<right:
                mid=(left+right)//2;pid,start=base.positions[mid];prefix=base.texts[pid][start:start+len(word)]
                if prefix<word or (after and prefix==word):left=mid+1
                else:right=mid
            bounds.append(left)
        for rank in range(*bounds):
            pid,start=base.positions[rank];ends[pid][start].add(start+len(word))
    return ends


def heap_paths(texts,q,denominator,ends):
    """Independent DP: one heap per bin, retaining dominated endpoints."""
    paths={}
    for pid,text in sorted(texts.items()):
        n=len(text);distance=[None]*n+[0];heaps=[[] for _ in BINS]
        for start in range(n-1,-1,-1):
            values=[]
            for b,(low,high) in enumerate(BINS):
                first=start+low;last=n if high is None else min(n,start+high);heap=heaps[b]
                if first<=n and distance[first] is not None:heapq.heappush(heap,(distance[first],first))
                removed=[]
                # Endpoints enter at the lower boundary and expire at the upper.
                # Buried expired endpoints remain until they reach the minimum.
                while heap:
                    value,end=heap[0]
                    if end>last:heapq.heappop(heap)
                    elif end in ends[pid][start]:removed.append(heapq.heappop(heap))
                    else:break
                if heap:values.append(heap[0][0]+q[pid][start][b]+(9 if low==1 else -1)*denominator)
                for item in removed:heapq.heappush(heap,item)
            if values:distance[start]=min(values)
        if distance[0] is None:raise ValueError('full allowed pool cannot cover a source')
        paths[pid]=distance[0]
    return paths


def verify(index,q,capacity=256,denominator=1000000):
    """Validate parent completeness, exact splitting, top multiplicities and heap DP."""
    validate_q(index.texts,q,capacity,denominator)
    base=index.base;assert index.texts==base.texts
    # Item33's independent suffix/LCP/ban/group completeness verifier, with zero
    # multipliers, validates the unchanged full candidate universe.
    parent.verify(base,{pid:[0]*len(t) for pid,t in base.texts.items()},0,1)
    expected=[]
    for gid,g in enumerate(base.groups):
        at=g['first']
        while at<=g['last']:
            b=bin_index(at);upper=BINS[b][1];last=g['last'] if upper is None else min(upper,g['last'])
            excluded=sorted(length for length in g['excluded_lengths'] if at<=length<=last)
            expected.append({'group':gid,'bin':b,'lo':g['lo'],'hi':g['hi'],'first':at,'last':last,
                             'excluded_lengths':excluded,'multiplicity':last-at+1-len(excluded)})
            at=last+1
    assert expected==index.pieces
    by_bin=[[] for _ in BINS]
    for k,p in enumerate(expected):by_bin[p['bin']].append(k)
    assert by_bin==index.by_bin
    assert index.distinct_allowed_entries==base.distinct_allowed_entries==sum(p['multiplicity'] for p in expected)
    weighted=[]
    for b in range(len(BINS)):
        prefix=[0]
        for pid,start in base.positions:prefix.append(prefix[-1]+q[pid][start][b])
        for k in by_bin[b]:
            p=expected[k];weighted.append((prefix[p['hi']]-prefix[p['lo']],p['multiplicity']))
    remaining=capacity;top=0
    for value,multiplicity in sorted(weighted,reverse=True):
        take=min(remaining,multiplicity);top+=take*value;remaining-=take
        if remaining==0:break
    endpoints=independently_relocate_bans(base)
    assert endpoints==base.banned_ends
    paths=heap_paths(base.texts,q,denominator,endpoints)
    return sum(paths.values())-top
