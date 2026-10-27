# Original candidate. Contract: https://leetcode.com/problems/sum-of-matrix-after-queries/
def solve(n, queries):
    seen=[set(),set()];answer=0
    for typ,index,value in reversed(queries):
        if index not in seen[typ]:answer+=(n-len(seen[1-typ]))*value;seen[typ].add(index)
    return answer
