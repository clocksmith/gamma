"""Original LeetCode 707 candidate; qualification unknown."""

class _Node:
    def __init__(self, val=0, next=None): self.val, self.next = val, next

class MyLinkedList:
    def __init__(self): self.head, self.size = _Node(), 0; self.tail = self.head
    def get(self, index):
        if index < 0 or index >= self.size: return -1
        node = self.head.next
        for _ in range(index): node = node.next
        return node.val
    def addAtHead(self, val): self.addAtIndex(0, val)
    def addAtTail(self, val):
        self.tail.next = _Node(val); self.tail = self.tail.next; self.size += 1
    def addAtIndex(self, index, val):
        if index > self.size: return
        index = max(index, 0)
        if index == self.size: self.addAtTail(val); return
        previous = self.head
        for _ in range(index): previous = previous.next
        previous.next = _Node(val, previous.next); self.size += 1
    def deleteAtIndex(self, index):
        if index < 0 or index >= self.size: return
        previous = self.head
        for _ in range(index): previous = previous.next
        previous.next = previous.next.next
        if index == self.size - 1: self.tail = previous
        self.size -= 1


def solve(operations, arguments):
    instance = MyLinkedList(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result
