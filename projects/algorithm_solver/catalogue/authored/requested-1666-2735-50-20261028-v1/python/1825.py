"""Original candidate; no qualification or admission."""

from collections import deque

class MKAverage:
    def __init__(self,m,k):self.m=m;self.k=k;self.queue=deque();self.count=[0]*100001;self.sums=[0]*100001
    def _add(self,value,delta):
        i=value
        while i<=100000:self.count[i]+=delta;self.sums[i]+=value*delta;i+=i&-i
    def addElement(self,num):
        if len(self.queue)==self.m:self._add(self.queue.popleft(),-1)
        self.queue.append(num);self._add(num,1)
    def _sum_first(self,k):
        i=count=total=0;bit=65536
        while bit:
            nxt=i+bit
            if nxt<=100000 and count+self.count[nxt]<=k:i=nxt;count+=self.count[nxt];total+=self.sums[nxt]
            bit//=2
        return total+(k-count)*(i+1)
    def calculateMKAverage(self):
        if len(self.queue)<self.m:return -1
        return (self._sum_first(self.m-self.k)-self._sum_first(self.k))//(self.m-2*self.k)


def solve(operations, arguments):
    instance = MKAverage(*arguments[0])
    out = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        out.append(getattr(instance, operation)(*values))
    return out
