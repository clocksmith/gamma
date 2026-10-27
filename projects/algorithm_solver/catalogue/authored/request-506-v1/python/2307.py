# Original candidate. Contract: https://leetcode.com/problems/check-for-contradictions-in-equations/
def solve(equations, values):
    graph={}
    for (a,b),value in zip(equations,values):
        stack=[(a,1.0)];seen={a};found=None
        while stack:
            u,ratio=stack.pop()
            if u==b:found=ratio;break
            for v,w in graph.get(u,[]):
                if v not in seen:seen.add(v);stack.append((v,ratio*w))
        if found is not None and abs(found-value)>=1e-5:return True
        graph.setdefault(a,[]).append((b,value));graph.setdefault(b,[]).append((a,1/value))
    return False
