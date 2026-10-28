from collections import deque


class MyStack:
    def __init__(self):
        self.queue = deque()

    def push(self, x):
        size = len(self.queue)
        self.queue.append(x)
        for _ in range(size):
            self.queue.append(self.queue.popleft())

    def pop(self):
        return self.queue.popleft()

    def top(self):
        return self.queue[0]

    def empty(self):
        return not self.queue
