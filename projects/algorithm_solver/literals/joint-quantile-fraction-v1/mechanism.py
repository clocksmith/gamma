"""Synthetic mechanism only. No corpus loader, optimizer, or execution contract."""
import heapq
import importlib.util
from pathlib import Path

_spec=importlib.util.spec_from_file_location('quantile_parent35',Path(__file__).resolve().parents[1]/'length-sensitive-fraction-v1/implicit.py')
parent=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(parent)
parent.require_checks()


def exact_caps(texts,q,denominator,ends,maximum=96):
    """Exact <=k costs from rolling exact-cardinality layers; no path expansion."""
    result={}
    for pid,text in sorted(texts.items()):
        n=len(text);previous=[None]*n+[0];best=None;values=[None]
        for count in range(1,min(maximum,n)+1):
            current=[None]*(n+1);heaps=[[] for _ in parent.BINS]
            for start in range(n-1,-1,-1):
                chosen=None
                for b,(low,high) in enumerate(parent.BINS):
                    first=start+low;last=n if high is None else min(n,start+high);heap=heaps[b]
                    if first<=n and previous[first] is not None:heapq.heappush(heap,(previous[first],first))
                    removed=[]
                    while heap:
                        cost,end=heap[0]
                        if end>last:heapq.heappop(heap)
                        elif end in ends[pid][start]:removed.append(heapq.heappop(heap))
                        else:break
                    if heap:
                        value=heap[0][0]+q[pid][start][b]+denominator*(9 if b==0 else -1)
                        if chosen is None or value<chosen:chosen=value
                    for item in removed:heapq.heappush(heap,item)
                current[start]=chosen
            if current[0] is not None:best=current[0] if best is None else min(best,current[0])
            values.append(best);previous=current
        values.extend([best]*(maximum+1-len(values)));result[pid]=values
    return result


def penalty_caps(texts,q,denominator,ends,penalties,caps=(32,96)):
    """Integer Lagrangian lower bounds on capped path costs; includes t=0."""
    assert penalties and 0 in penalties and len(set(penalties))==len(penalties)
    assert all(type(t) is int and t>=0 for t in penalties)
    result={pid:{k:None for k in caps} for pid in texts};unrestricted=None
    for t in penalties:
        shifted=q if t==0 else {pid:[[v+t for v in row] for row in rows] for pid,rows in q.items()}
        paths=parent.heap_paths(texts,shifted,denominator,ends)
        if t==0:unrestricted=paths
        for pid,cost in paths.items():
            for cap in caps:
                value=cost-t*cap;old=result[pid][cap]
                result[pid][cap]=value if old is None else max(old,value)
    return result,unrestricted


def three_class_assignment(costs,short_count,medium_count,free_count):
    """Exact integer DP; only short/free counts are explicit state dimensions."""
    assert len(costs)==short_count+medium_count+free_count
    stride=free_count+1;dp=[None]*((short_count+1)*stride);dp[0]=0
    for index,row in enumerate(costs):
        assert len(row)==3
        nxt=[None]*len(dp)
        for short in range(min(index,short_count)+1):
            for free in range(min(index-short,free_count)+1):
                medium=index-short-free
                if medium>medium_count:continue
                at=short*stride+free;value=dp[at]
                if value is None:continue
                moves=((short<short_count,at+stride,row[0]),(medium<medium_count,at,row[1]),(free<free_count,at+1,row[2]))
                for allowed,target,cost in moves:
                    if allowed and cost is not None:
                        candidate=value+cost
                        if nxt[target] is None or candidate<nxt[target]:nxt[target]=candidate
        dp=nxt
    return dp[short_count*stride+free_count]


def assignment_flow(costs,counts):
    """Small exact-integer transportation solver, independent of the count DP."""
    n=len(costs);k=len(counts);assert sum(counts)==n and all(len(row)==k for row in costs)
    source=n+k;sink=source+1;graph=[[] for _ in range(sink+1)];refs={};offset=0
    def edge(a,b,capacity,cost):
        forward=[b,len(graph[b]),capacity,cost];back=[a,len(graph[a]),0,-cost]
        graph[a].append(forward);graph[b].append(back);return forward
    for p,row in enumerate(costs):
        finite=[v for v in row if v is not None]
        if not finite:return None
        low=min(finite);offset+=low;edge(source,p,1,0)
        for label,cost in enumerate(row):
            if cost is not None:refs[p,label]=edge(p,n+label,1,cost-low)
    for label,count in enumerate(counts):edge(n+label,sink,count,0)
    potentials=[0]*len(graph);total=offset
    for _ in range(n):
        distance=[None]*len(graph);distance[source]=0;back=[None]*len(graph);queue=[(0,source)]
        while queue:
            value,at=heapq.heappop(queue)
            if distance[at]!=value:continue
            for i,e in enumerate(graph[at]):
                target,rev,capacity,cost=e
                if not capacity:continue
                reduced=cost+potentials[at]-potentials[target];assert reduced>=0
                new=value+reduced
                if distance[target] is None or new<distance[target]:
                    distance[target]=new;back[target]=(at,i);heapq.heappush(queue,(new,target))
        if distance[sink] is None:return None
        for i,value in enumerate(distance):
            if value is not None:potentials[i]+=value
        at=sink
        while at!=source:
            previous,index=back[at];e=graph[previous][index]
            total+=e[3];e[2]-=1;graph[at][e[1]][2]+=1;at=previous
    assigned=[next(label for label in range(k) if (p,label) in refs and refs[p,label][2]==0) for p in range(n)]
    assert [assigned.count(label) for label in range(k)]==counts
    assert total==sum(costs[p][label] for p,label in enumerate(assigned))
    # Independent exact assignment-dual check via only k category potentials.
    v=[0]*k
    for _ in range(k):
        changed=False
        for p,a in enumerate(assigned):
            for b,cost in enumerate(costs[p]):
                if cost is not None and v[b]>v[a]+cost-costs[p][a]:
                    v[b]=v[a]+cost-costs[p][a];changed=True
        if not changed:break
    u=[costs[p][a]-v[a] for p,a in enumerate(assigned)]
    assert all(u[p]+v[b]<=cost for p,row in enumerate(costs) for b,cost in enumerate(row) if cost is not None)
    assert total==sum(u)+sum(count*value for count,value in zip(counts,v))
    return total


def exact_median_assignment(caps,unrestricted):
    """300 programs: exact average-of-central-pair median <=32 and p95<=96."""
    assert len(caps)==len(unrestricted)==300 and set(caps)==set(unrestricted)
    costs=[]
    for a in range(1,33):
        rows=[[caps[p][a],caps[p][64-a],caps[p][96],unrestricted[p]] for p in sorted(caps)]
        costs.append(assignment_flow(rows,[150,1,134,15]))
    finite=[v for v in costs if v is not None]
    return min(finite) if finite else None,costs
