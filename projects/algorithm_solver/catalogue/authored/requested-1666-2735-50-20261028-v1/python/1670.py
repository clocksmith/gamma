"""Original candidate; no qualification or admission."""

from collections import deque

class FrontMiddleBackQueue:
    def __init__(self):self.left=deque();self.right=deque()
    def _balance(self):
        if len(self.left)<len(self.right):self.left.append(self.right.popleft())
        elif len(self.left)>len(self.right)+1:self.right.appendleft(self.left.pop())
    def pushFront(self,val):self.left.appendleft(val);self._balance()
    def pushMiddle(self,val):
        if len(self.left)>len(self.right):self.right.appendleft(self.left.pop())
        self.left.append(val)
    def pushBack(self,val):self.right.append(val);self._balance()
    def popFront(self):
        if not self.left:return -1
        value=self.left.popleft();self._balance();return value
    def popMiddle(self):
        if not self.left:return -1
        value=self.left.pop();self._balance();return value
    def popBack(self):
        if not self.left:return -1
        value=self.right.pop() if self.right else self.left.pop();self._balance();return value


def solve(operations, arguments):
    instance = FrontMiddleBackQueue(*arguments[0])
    out = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        out.append(getattr(instance, operation)(*values))
    return out
