"""Separate O(n log n) dry-day successor variant; owned DSU skips used days."""
from bisect import bisect_right
def solve(rains: list[int]) -> list[int]:
    dry=[day for day,lake in enumerate(rains) if not lake]
    parent=list(range(len(dry)+1))
    def find(i):
        root=i
        while parent[root]!=root:
            root=parent[root]
        while parent[i]!=i:
            nxt=parent[i]
            parent[i]=root
            i=nxt
        return root
    answer=[-1 if lake else 1 for lake in rains]
    last={}
    for day,lake in enumerate(rains):
        if not lake:
            continue
        if lake in last:
            slot=find(bisect_right(dry,last[lake]))
            if slot==len(dry) or dry[slot]>=day:
                return []
            answer[dry[slot]]=lake
            parent[slot]=find(slot+1)
        last[lake]=day
    return answer
class Solution:
    def avoidFlood(self,rains: list[int]) -> list[int]:
        return solve(rains)
