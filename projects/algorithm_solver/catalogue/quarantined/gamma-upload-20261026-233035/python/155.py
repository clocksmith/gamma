"""155. Min Stack."""
class MinStack:
    def __init__(self):
        self.values = []
        self.minimums = []

    def push(self, val: int) -> None:
        self.values.append(val)
        self.minimums.append(val if not self.minimums else min(val, self.minimums[-1]))

    def pop(self) -> None:
        self.values.pop()
        self.minimums.pop()

    def top(self) -> int:
        return self.values[-1]

    def getMin(self) -> int:
        return self.minimums[-1]

def solve(operations: list[str], arguments: list[list[int]]) -> list:
    stack = MinStack()
    result = []
    for operation, values in zip(operations, arguments):
        if operation == 'MinStack':
            result.append(None)
        else:
            result.append(getattr(stack, operation)(*values))
    return result
