class MinStack:
    def __init__(self):
        self.head = None

    def push(self, value):
        minimum = value if self.head is None else min(value, self.head[1])
        self.head = (value, minimum, self.head)

    def pop(self):
        self.head = self.head[2]

    def top(self):
        return self.head[0]

    def getMin(self):
        return self.head[1]
