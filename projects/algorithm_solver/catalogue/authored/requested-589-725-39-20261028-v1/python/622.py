"""Original LeetCode 622 candidate; qualification unknown."""

class MyCircularQueue:
    def __init__(self, k):
        self.data, self.head, self.size = [0] * k, 0, 0
    def enQueue(self, value):
        if self.isFull(): return False
        self.data[(self.head + self.size) % len(self.data)] = value
        self.size += 1
        return True
    def deQueue(self):
        if self.isEmpty(): return False
        self.head = (self.head + 1) % len(self.data)
        self.size -= 1
        return True
    def Front(self): return -1 if self.isEmpty() else self.data[self.head]
    def Rear(self): return -1 if self.isEmpty() else self.data[(self.head + self.size - 1) % len(self.data)]
    def isEmpty(self): return self.size == 0
    def isFull(self): return self.size == len(self.data)


def solve(operations, arguments):
    instance = MyCircularQueue(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result
