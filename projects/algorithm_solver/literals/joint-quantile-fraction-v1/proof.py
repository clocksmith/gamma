"""Exact integer proof receipts and independent cardinality replay; no input loader."""
import bisect
import heapq
import mechanism


def infeasibility(costs,counts):
    # Hall's theorem on category-demand copies. There are only 15 subsets.
    for mask in range(1,1<<len(counts)):
        demand=sum(count for label,count in enumerate(counts) if mask>>label&1)
        neighbors=sum(any(cost is not None and mask>>label&1 for label,cost in enumerate(row)) for row in costs)
        if demand>neighbors:
            result={'feasible':False,'hall_subset':mask,'demand':demand,'neighbors':neighbors}
            verify_assignment(costs,counts,result)
            return result
    raise AssertionError('No assignment but no Hall infeasibility certificate')


def verify_assignment(costs,counts,receipt):
    mechanism.parent.require_checks()
    n=len(costs);k=len(counts)
    assert sum(counts)==n and all(type(c) is int and c>=0 for c in counts)
    assert all(len(row)==k and all(c is None or type(c) is int for c in row) for row in costs)
    assert type(receipt['feasible']) is bool
    if not receipt['feasible']:
        assert set(receipt)=={'feasible','hall_subset','demand','neighbors'}
        mask=receipt['hall_subset'];assert type(mask) is int and 0<mask<1<<k
        demand=sum(count for label,count in enumerate(counts) if mask>>label&1)
        neighbors=sum(any(cost is not None and mask>>label&1 for label,cost in enumerate(row)) for row in costs)
        assert type(receipt['demand']) is int and type(receipt['neighbors']) is int
        assert receipt['demand']==demand and receipt['neighbors']==neighbors and demand>neighbors
        return None
    assert set(receipt)=={'feasible','value','assignment','row_potentials','category_potentials'}
    a=receipt['assignment'];u=receipt['row_potentials'];v=receipt['category_potentials']
    assert len(a)==len(u)==n and len(v)==k
    assert all(type(x) is int for x in a+u+v) and type(receipt['value']) is int
    assert all(0<=x<k for x in a) and [a.count(c) for c in range(k)]==counts
    assert all(costs[p][c] is not None for p,c in enumerate(a))
    primal=sum(costs[p][c] for p,c in enumerate(a))
    assert all(u[p]+v[c]<=cost for p,row in enumerate(costs) for c,cost in enumerate(row) if cost is not None)
    dual=sum(u)+sum(count*x for count,x in zip(counts,v))
    assert receipt['value']==primal==dual
    return primal


def assignment_proof(costs,counts):
    """Small exact-integer transportation solver, independent of the count DP."""
    n=len(costs);k=len(counts);assert sum(counts)==n and all(len(row)==k for row in costs)
    source=n+k;sink=source+1;graph=[[] for _ in range(sink+1)];refs={};offset=0
    def edge(a,b,capacity,cost):
        forward=[b,len(graph[b]),capacity,cost];back=[a,len(graph[a]),0,-cost]
        graph[a].append(forward);graph[b].append(back);return forward
    for p,row in enumerate(costs):
        finite=[v for v in row if v is not None]
        if not finite:return infeasibility(costs,counts)
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
        if distance[sink] is None:return infeasibility(costs,counts)
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
    result={'feasible':True,'value':total,'assignment':assigned,'row_potentials':u,'category_potentials':v}
    verify_assignment(costs,counts,result)
    return result



def tree_caps(texts,q,denominator,ends,maximum=96):
    """Independent static segment tree per cardinality, with split ban windows."""
    answer={}
    def minimum(a,b):return b if a is None else a if b is None else min(a,b)
    for pid,text in sorted(texts.items()):
        n=len(text);previous=[None]*n+[0];best=None;caps=[None]
        blocked=[sorted(row) for row in ends[pid]]
        size=1
        while size<n+1:size*=2
        for count in range(1,min(maximum,n)+1):
            tree=[None]*size+previous+[None]*(size-n-1)
            for at in range(size-1,0,-1):tree[at]=minimum(tree[2*at],tree[2*at+1])
            def query(left,right):
                value=None;left+=size;right+=size
                while left<right:
                    if left&1:value=minimum(value,tree[left]);left+=1
                    if right&1:right-=1;value=minimum(value,tree[right])
                    left//=2;right//=2
                return value
            current=[None]*(n+1)
            for start in range(n):
                for b,(lo,hi) in enumerate(mechanism.parent.BINS):
                    left=start+lo;right=min(n,start+hi) if hi is not None else n
                    if left>right:continue
                    value=None;cursor=left;ban=blocked[start]
                    first=bisect.bisect_left(ban,left);last=bisect.bisect_right(ban,right)
                    for end in ban[first:last]:value=minimum(value,query(cursor,end));cursor=end+1
                    value=minimum(value,query(cursor,right+1))
                    if value is not None:
                        value+=q[pid][start][b]+denominator*(9 if b==0 else -1)
                        current[start]=minimum(current[start],value)
            best=minimum(best,current[0]);caps.append(best);previous=current
        caps.extend([best]*(maximum+1-len(caps)));answer[pid]=caps
    return answer


def build_assignments(caps,unrestricted):
    assert len(caps)==len(unrestricted)==300 and set(caps)==set(unrestricted)
    ids=sorted(caps)
    necessary=assignment_proof([[caps[p][32],caps[p][96],unrestricted[p]] for p in ids],[150,135,15])
    cases=[]
    for a in range(1,33):
        rows=[[caps[p][a],caps[p][64-a],caps[p][96],unrestricted[p]] for p in ids]
        cases.append(assignment_proof(rows,[150,1,134,15]))
    return {'necessary':necessary,'median_cases':cases}


def verify_assignments(caps,unrestricted,receipts):
    assert len(caps)==len(unrestricted)==300 and set(caps)==set(unrestricted)
    assert set(receipts)=={'necessary','median_cases'} and len(receipts['median_cases'])==32
    ids=sorted(caps)
    necessary=verify_assignment([[caps[p][32],caps[p][96],unrestricted[p]] for p in ids],[150,135,15],receipts['necessary'])
    values=[]
    for a,receipt in enumerate(receipts['median_cases'],1):
        rows=[[caps[p][a],caps[p][64-a],caps[p][96],unrestricted[p]] for p in ids]
        values.append(verify_assignment(rows,[150,1,134,15],receipt))
    finite=[v for v in values if v is not None]
    exact=min(finite) if finite else None
    assert necessary is None or necessary>=sum(unrestricted.values())
    assert exact is None or (necessary is not None and exact>=necessary)
    return necessary,exact
