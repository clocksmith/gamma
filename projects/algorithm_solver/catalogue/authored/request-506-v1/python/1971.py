# Original candidate. Contract: https://leetcode.com/problems/find-if-path-exists-in-graph/
def solve(n, edges, source, destination):
    parent=list(range(n)); size=[1]*n
    def find(x):
        while x!=parent[x]:
            parent[x]=parent[parent[x]]; x=parent[x]
        return x
    for a,b in edges:
        a,b=find(a),find(b)
        if a!=b:
            if size[a]<size[b]:a,b=b,a
            parent[b]=a;size[a]+=size[b]
    return find(source)==find(destination)
