"""Original candidate; no qualification or admission."""

import heapq

class SeatManager:
    def __init__(self,n):self.next=1;self.free=[]
    def reserve(self):
        if self.free:return heapq.heappop(self.free)
        value=self.next;self.next+=1;return value
    def unreserve(self,seatNumber):heapq.heappush(self.free,seatNumber)


def solve(operations, arguments):
    instance = SeatManager(*arguments[0])
    out = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        out.append(getattr(instance, operation)(*values))
    return out
