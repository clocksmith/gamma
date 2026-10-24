"""Invented-input exact joint supergradient prototype. No file/input loader."""
from array import array
import heapq
import importlib.util
from pathlib import Path
import sys
import time

PARENT=Path(__file__).resolve().parents[1]/'joint-quantile-fraction-v1'
_path=list(sys.path);sys.path.insert(0,str(PARENT))
try:
    _spec=importlib.util.spec_from_file_location('joint_ascent_proof',PARENT/'proof.py')
    assignment=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(assignment)
finally:sys.path[:]=_path
mechanism=assignment.mechanism;dual=mechanism.parent
dual.require_checks()
ENDPOINT_BYTES=64*1024**2
SENTINEL=2**32-1
assert array('I').itemsize==4


def zeros(texts):return {p:[[0]*len(dual.BINS) for _ in t] for p,t in texts.items()}


def dot(a,b):return sum(x*y for p in a for row,other in zip(a[p],b[p]) for x,y in zip(row,other))


def recover(text,q,blocked,denominator,exact_count=None,endpoint_bytes=ENDPOINT_BYTES):
    """Sequential-program exact layers; compact endpoints, rolling cost arrays."""
    n=len(text);assert 0<n<SENTINEL
    if exact_count is not None:assert type(exact_count) is int and 1<=exact_count<=n
    layers=exact_count if exact_count is not None else 1
    requested=layers*(n+1)*4
    if requested>endpoint_bytes:raise MemoryError('Explicit endpoint-byte cap exceeded')
    previous=[None]*n+[0];back=[]
    for layer in range(layers):
        current=[None]*(n+1);current[n]=0 if exact_count is None else None
        pointer=array('I',[SENTINEL])*(n+1);heaps=[[] for _ in dual.BINS]
        for start in range(n-1,-1,-1):
            choices=[];tail=current if exact_count is None else previous
            for b,(low,high) in enumerate(dual.BINS):
                first=start+low;last=n if high is None else min(n,start+high);heap=heaps[b]
                if first<=n and tail[first] is not None:heapq.heappush(heap,(tail[first],first))
                removed=[]
                while heap:
                    cost,end=heap[0]
                    if end>last:heapq.heappop(heap)
                    elif end in blocked[start]:removed.append(heapq.heappop(heap))
                    else:break
                if heap:
                    cost,end=heap[0];choices.append((cost+q[start][b]+denominator*(9 if b==0 else -1),end))
                for entry in removed:heapq.heappush(heap,entry)
            if choices:current[start],pointer[start]=min(choices)
        back.append(pointer);previous=current
    if previous[0] is None:raise ValueError('No path at requested cardinality')
    at=0;left=layers;edges=[]
    while at<n:
        end=back[left-1 if exact_count is not None else 0][at]
        assert at<end<=n and end not in blocked[at]
        b=dual.bin_index(end-at);edges.append((at,end,b));at=end
        if exact_count is not None:left-=1
    assert exact_count is None or left==0 and len(edges)==exact_count
    value=sum(denominator*(9 if b==0 else -1)+q[start][b] for start,end,b in edges)
    assert value==previous[0]
    return edges,value,requested


def joint_cases(caps,unrestricted,median_cap=32,p95_cap=96):
    ids=sorted(caps);n=len(ids);assert n%2==0 and n>=4
    rank=(95*n+99)//100;counts=[n//2,1,rank-n//2-1,n-rank]
    assert min(counts)>=0 and 2*median_cap-1<=p95_cap
    receipts=[]
    for a in range(1,median_cap+1):
        rows=[[caps[p][a],caps[p][2*median_cap-a],caps[p][p95_cap],unrestricted[p]] for p in ids]
        receipt=assignment.assignment_proof(rows,counts)
        assignment.verify_assignment(rows,counts,receipt);receipts.append(receipt)
    feasible=[(r['value'],a,r) for a,r in enumerate(receipts,1) if r['feasible']]
    if not feasible:return None,receipts
    value,a,receipt=min(feasible,key=lambda x:(x[0],x[1]))
    return (value,a,receipt,counts),receipts


def oracle(index,q,capacity=256,denominator=1000000,median_cap=32,p95_cap=96,endpoint_bytes=ENDPOINT_BYTES):
    """One complete joint oracle/gradient; timing includes every component."""
    started=time.monotonic();dual.validate_q(index.texts,q,capacity,denominator)
    caps=mechanism.exact_caps(index.texts,q,denominator,index.base.banned_ends,maximum=p95_cap)
    unrestricted=dual.heap_paths(index.texts,q,denominator,index.base.banned_ends)
    after_caps=time.monotonic()
    chosen,receipts=joint_cases(caps,unrestricted,median_cap,p95_cap)
    after_assignments=time.monotonic()
    if chosen is None:
        return {'joint_family_feasible':False,'assignments':receipts,'seconds':time.monotonic()-started}
    path_value,a,receipt,counts=chosen
    top,selected=index.weighted_selection(q,capacity)
    dictionary_occurrences=index.selected_occurrences(selected)
    assert dot(q,dictionary_occurrences)==top
    after_dictionary=time.monotonic()
    used=zeros(index.texts);paths={};peak_bytes=0;path_sizes=[];base_total=0
    for pid,label in zip(sorted(index.texts),receipt['assignment']):
        cap=(a,2*median_cap-a,p95_cap,None)[label]
        target=unrestricted[pid] if cap is None else caps[pid][cap]
        k=None if cap is None else next(k for k in range(1,cap+1) if caps[pid][k]==target)
        edges,value,back_bytes=recover(index.texts[pid],q[pid],index.base.banned_ends[pid],denominator,k,endpoint_bytes)
        assert value==target
        peak_bytes=max(peak_bytes,back_bytes);paths[pid]=edges;path_sizes.append(len(edges))
        for start,end,b in edges:
            assert used[pid][start][b]==0;used[pid][start][b]=1
            base_total+=9 if b==0 else -1
    sorted_sizes=sorted(path_sizes);n=len(path_sizes);rank=(95*n+99)//100
    assert sorted_sizes[n//2-1]+sorted_sizes[n//2]<=2*median_cap and sorted_sizes[rank-1]<=p95_cap
    assert denominator*base_total+dot(q,used)==path_value
    gradient={pid:[[x-y for x,y in zip(row,other)] for row,other in zip(used[pid],dictionary_occurrences[pid])] for pid in q}
    assert all(-capacity<=v<=1 for rows in gradient.values() for row in rows for v in row)
    finished=time.monotonic()
    return {'joint_family_feasible':True,'numerator':path_value-top,'denominator':denominator,
            'joint_path_numerator':path_value,'top_capacity_numerator':top,'selected_a':a,
            'selected_pieces':selected,'assignments':receipts,'paths':paths,'gradient':gradient,
            'F':base_total,'path_selections':path_sizes,'endpoint_peak_bytes':peak_bytes,
            'seconds':finished-started,'phase_seconds':{'cardinality_and_unrestricted':after_caps-started,
              'all_assignments':after_assignments-after_caps,'dictionary_weights_and_multiplicity':after_dictionary-after_assignments,
              'path_recovery_and_gradient':finished-after_dictionary}}


def update(q,gradient,step):
    assert type(step) is int and step>0
    assert set(q)==set(gradient)
    return {pid:[[max(0,x+step*g) for x,g in zip(row,other)] for row,other in zip(q[pid],gradient[pid])] for pid in q}
