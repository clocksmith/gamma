"""Original candidate; no qualification or admission."""

import heapq

class DinnerPlates:
    def __init__(self,capacity):self.capacity=capacity;self.stacks=[];self.available=[];self.right=-1
    def push(self,val):
        if not self.available:self.stacks.append([]);heapq.heappush(self.available,len(self.stacks)-1)
        index=self.available[0];self.stacks[index].append(val);self.right=max(self.right,index)
        if len(self.stacks[index])==self.capacity:heapq.heappop(self.available)
    def pop(self):return self.popAtStack(self.right)
    def popAtStack(self,index):
        if index<0 or index>=len(self.stacks) or not self.stacks[index]:return -1
        if len(self.stacks[index])==self.capacity:heapq.heappush(self.available,index)
        value=self.stacks[index].pop()
        while self.right>=0 and not self.stacks[self.right]:self.right-=1
        return value


def solve(operations, arguments):
    instance = DinnerPlates(*arguments[0])
    out = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        out.append(getattr(instance, operation)(*values))
    return out
