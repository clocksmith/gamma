# Original candidate. Contract: https://leetcode.com/problems/closest-nodes-queries-in-a-binary-search-tree/
def solve(root, queries):
    from bisect import bisect_left
    values=sorted(x for x in root if x is not None);out=[]
    for x in queries:
        i=bisect_left(values,x)
        if i<len(values) and values[i]==x:out.append([x,x])
        else:out.append([values[i-1] if i else -1,values[i] if i<len(values) else -1])
    return out
