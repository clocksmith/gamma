"""Original candidate; no qualification or admission."""

from bisect import bisect_left,bisect_right

class MajorityChecker:
    def __init__(self,arr):
        self.positions={};self.size=1
        while self.size<len(arr):self.size*=2
        self.tree=[(0,0)]*(2*self.size)
        for i,v in enumerate(arr):self.positions.setdefault(v,[]).append(i);self.tree[self.size+i]=(v,1)
        for i in range(self.size-1,0,-1):self.tree[i]=self._merge(self.tree[2*i],self.tree[2*i+1])
    @staticmethod
    def _merge(a,b):
        if a[0]==b[0]:return (a[0],a[1]+b[1])
        return (a[0],a[1]-b[1]) if a[1]>=b[1] else (b[0],b[1]-a[1])
    def query(self,left,right,threshold):
        lo,hi=left+self.size,right+self.size+1;candidate=(0,0)
        while lo<hi:
            if lo%2:candidate=self._merge(candidate,self.tree[lo]);lo+=1
            if hi%2:hi-=1;candidate=self._merge(candidate,self.tree[hi])
            lo//=2;hi//=2
        value=candidate[0];places=self.positions.get(value,[])
        return value if bisect_right(places,right)-bisect_left(places,left)>=threshold else -1


def solve(operations, arguments):
    instance = MajorityChecker(*arguments[0])
    out = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        out.append(getattr(instance, operation)(*values))
    return out
