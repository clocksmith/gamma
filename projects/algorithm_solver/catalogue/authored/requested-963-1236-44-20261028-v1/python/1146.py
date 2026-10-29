"""Original candidate; no qualification or admission."""

from bisect import bisect_right

class SnapshotArray:
    def __init__(self,length):self.history=[[(0,0)] for _ in range(length)];self.current=0
    def set(self,index,val):
        history=self.history[index]
        if history[-1][0]==self.current:history[-1]=(self.current,val)
        else:history.append((self.current,val))
    def snap(self):self.current+=1;return self.current-1
    def get(self,index,snap_id):
        history=self.history[index];return history[bisect_right(history,(snap_id,10**9+1))-1][1]


def solve(operations, arguments):
    instance = SnapshotArray(*arguments[0])
    out = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        out.append(getattr(instance, operation)(*values))
    return out
