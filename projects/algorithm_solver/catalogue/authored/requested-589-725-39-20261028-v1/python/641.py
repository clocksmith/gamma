"""Original LeetCode 641 candidate; qualification unknown."""

class MyCircularDeque:
    def __init__(self, k): self.data, self.head, self.size = [0] * k, 0, 0
    def insertFront(self, value):
        if self.isFull(): return False
        self.head = (self.head - 1) % len(self.data)
        self.data[self.head] = value
        self.size += 1
        return True
    def insertLast(self, value):
        if self.isFull(): return False
        self.data[(self.head + self.size) % len(self.data)] = value
        self.size += 1
        return True
    def deleteFront(self):
        if self.isEmpty(): return False
        self.head = (self.head + 1) % len(self.data)
        self.size -= 1
        return True
    def deleteLast(self):
        if self.isEmpty(): return False
        self.size -= 1
        return True
    def getFront(self): return -1 if self.isEmpty() else self.data[self.head]
    def getRear(self): return -1 if self.isEmpty() else self.data[(self.head + self.size - 1) % len(self.data)]
    def isEmpty(self): return self.size == 0
    def isFull(self): return self.size == len(self.data)


def solve(operations, arguments):
    instance = MyCircularDeque(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result
