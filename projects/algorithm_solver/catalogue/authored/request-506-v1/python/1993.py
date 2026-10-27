"""Original candidate for LeetCode 1993. Contract: https://leetcode.com/problems/operations-on-tree/
Development tests only; not admitted or independently qualified.
Batch adapter solve(operations, arguments) follows official class-call arrays, constructor result null.
Complexity: O(n) per upgrade, O(1) lock/unlock, O(n+q) space"""
def solve(operations,arguments):
    parent=arguments[0][0];children=[[] for _ in parent];locked=[0]*len(parent)
    for i in range(1,len(parent)):children[parent[i]].append(i)
    out=[None]
    for op,args in zip(operations[1:],arguments[1:]):
        node,user=args
        if op=='lock':
            ok=not locked[node]
            if ok:locked[node]=user
        elif op=='unlock':
            ok=locked[node]==user
            if ok:locked[node]=0
        else:
            p=node;ok=True
            while p!=-1:
                if locked[p]:ok=False;break
                p=parent[p]
            descendants=[];stack=children[node][:]
            while stack:
                v=stack.pop();descendants.append(v);stack.extend(children[v])
            ok=ok and any(locked[v] for v in descendants)
            if ok:
                for v in descendants:locked[v]=0
                locked[node]=user
        out.append(bool(ok))
    return out
