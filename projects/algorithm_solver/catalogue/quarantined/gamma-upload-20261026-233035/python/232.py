"""232. Implement Queue using Stacks."""
class MyQueue:
    def __init__(self):
        self.input = []
        self.output = []

    def push(self, x: int) -> None:
        self.input.append(x)

    def _move(self) -> None:
        if not self.output:
            while self.input:
                self.output.append(self.input.pop())

    def pop(self) -> int:
        self._move()
        return self.output.pop()

    def peek(self) -> int:
        self._move()
        return self.output[-1]

    def empty(self) -> bool:
        return not self.input and not self.output

def solve(operations: list[str], arguments: list[list[int]]) -> list:
    queue = MyQueue()
    result = []
    for operation, values in zip(operations, arguments):
        if operation == 'MyQueue':
            result.append(None)
        else:
            result.append(getattr(queue, operation)(*values))
    return result
