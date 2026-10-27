# Original candidate implementation. Contract: https://leetcode.com/problems/count-nodes-with-the-highest-score/
def solve(parents):
    n=len(parents);children=[[] for _ in parents]
    for i in range(1,n):children[parents[i]].append(i)
    order=[0]
    for u in order:order.extend(children[u])
    size=[1]*n;best=count=0
    for u in reversed(order):
        product=1
        for v in children[u]:size[u]+=size[v];product*=size[v]
        if n>size[u]:product*=n-size[u]
        if product>best:best=product;count=1
        elif product==best:count+=1
    return count
