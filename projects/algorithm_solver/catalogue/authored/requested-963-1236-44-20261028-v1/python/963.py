"""Original candidate; no qualification or admission."""

from collections import defaultdict
from itertools import combinations

def solve(points):
    diagonals = defaultdict(list)
    for i,(x,y) in enumerate(points):
        for j in range(i):
            a,b=points[j]
            diagonals[x+a,y+b,(x-a)**2+(y-b)**2].append((i,j))
    best = None
    for group in diagonals.values():
        for (i,j),(k,_) in combinations(group,2):
            a,b,c=points[i],points[j],points[k]
            area=abs((a[0]-c[0])*(b[1]-c[1])-(a[1]-c[1])*(b[0]-c[0]))
            if area and (best is None or area<best): best=area
    return 0 if best is None else best


class Solution:
    def minAreaFreeRect(self, points):
        return solve(points)
