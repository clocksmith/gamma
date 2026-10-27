"""225. Implement Stack using Queues."""
from collections import deque

class MyStack:
    def __init__(self):
        self.queue = deque()

    def push(self, x: int) -> None:
        self.queue.append(x)
        for _ in range(len(self.queue) - 1):
            self.queue.append(self.queue.popleft())

    def pop(self) -> int:
        return self.queue.popleft()

    def top(self) -> int:
        return self.queue[0]

    def empty(self) -> bool:
        return not self.queue

def solve(operations: list[str], arguments: list[list[int]]) -> list:
    stack = MyStack()
    result = []
    for operation, values in zip(operations, arguments):
        if operation == 'MyStack':
            result.append(None)
        else:
            result.append(getattr(stack, operation)(*values))
    return result
