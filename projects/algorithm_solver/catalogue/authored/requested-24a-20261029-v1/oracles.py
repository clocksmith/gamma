"""Small independent references; maximum cases use separate analytic expectations."""
from collections import deque

class TreeNode:
    def __init__(self,val=0,left=None,right=None):self.val,self.left,self.right=val,left,right

def make_tree(flat):
    if not flat:return None
    nodes=[TreeNode(v) for v,l,r in flat]
    for node,(v,l,r) in zip(nodes,flat):node.left=nodes[l] if l is not None else None;node.right=nodes[r] if r is not None else None
    return nodes[0]

def validate_domain(pid,args):
    def integer(x,lo,hi):assert type(x) is int and lo<=x<=hi
    if pid==1530:
        flat,d=args;integer(len(flat),1,1024);integer(d,1,10);parents=[0]*len(flat)
        for v,l,r in flat:
            integer(v,1,100)
            for j in (l,r):
                if j is not None:integer(j,1,len(flat)-1);parents[j]+=1
        assert parents[0]==0 and all(x==1 for x in parents[1:])
        seen={0};q=[0]
        for i in q:
            for j in flat[i][1:]:
                if j is not None:assert j not in seen;seen.add(j);q.append(j)
        assert len(seen)==len(flat)
    elif pid==1600:
        ops,rows=args;assert ops[0]=='ThroneInheritance' and len(rows[0])==1
        assert len(ops)==len(rows);names={rows[0][0]};dead=set();mutations=queries=0
        for op,row in zip(ops[1:],rows[1:]):
            if op=='birth':assert len(row)==2 and row[0] in names and row[0] not in dead and row[1] not in names;names.add(row[1]);mutations+=1
            elif op=='death':assert len(row)==1 and row[0] in names;dead.add(row[0]);mutations+=1
            else:assert op=='getInheritanceOrder' and row==[];queries+=1
        assert mutations<=100000 and queries<=10
        assert all(1<=len(name)<=15 and all('a'<=ch<='z' for ch in name) for name in names)
    elif pid==1603:
        ops,rows=args;assert ops[0]=='ParkingSystem' and len(rows[0])==3 and len(ops)==len(rows)
        for x in rows[0]:integer(x,0,1000)
        assert len(ops)-1<=1000
        for op,row in zip(ops[1:],rows[1:]):assert op=='addCar' and len(row)==1;integer(row[0],1,3)
    else:raise ValueError(pid)

def reference(pid,args):
    validate_domain(pid,args)
    if pid==1530:
        flat,limit=args;g=[[] for _ in flat];leaves=[]
        for i,(v,l,r) in enumerate(flat):
            if l is None and r is None:leaves.append(i)
            for j in (l,r):
                if j is not None:g[i].append(j);g[j].append(i)
        answer=0
        for index,leaf in enumerate(leaves):
            distance={leaf:0};q=deque([leaf])
            while q:
                u=q.popleft()
                for v in g[u]:
                    if v not in distance:distance[v]=distance[u]+1;q.append(v)
            answer+=sum(distance[other]<=limit for other in leaves[index+1:])
        return answer
    if pid==1600:
        ops,rows=args;king=rows[0][0];order=[king];parent={king:None};dead=set();out=[None]
        for op,row in zip(ops[1:],rows[1:]):
            if op=='birth':
                p,child=row;position=order.index(p)+1
                while position<len(order):
                    ancestor=parent[order[position]]
                    while ancestor is not None and ancestor!=p:ancestor=parent[ancestor]
                    if ancestor!=p:break
                    position+=1
                order.insert(position,child);parent[child]=p;out.append(None)
            elif op=='death':dead.add(row[0]);out.append(None)
            else:out.append([x for x in order if x not in dead])
        return out
    if pid==1603:
        ops,rows=args;spaces=[[False]*count for count in rows[0]];out=[None]
        for row in rows[1:]:
            slots=spaces[row[0]-1]
            try:index=slots.index(False)
            except ValueError:out.append(False)
            else:slots[index]=True;out.append(True)
        return out
