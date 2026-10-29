"""Original frontend 1381 variant; qualification unknown."""


class CustomStack:
    def __init__(self, maxSize: int):
        self.cap = maxSize
        self.stk = []
        self.inc = [0] * maxSize

    def push(self, x: int) -> None:
        if len(self.stk) < self.cap:
            self.stk.append(x)

    def pop(self) -> int:
        if not self.stk:
            return -1
        i = len(self.stk) - 1
        add = self.inc[i]
        if i > 0:
            self.inc[i - 1] += add
        self.inc[i] = 0
        return self.stk.pop() + add

    def increment(self, k: int, val: int) -> None:
        idx = min(k, len(self.stk)) - 1
        if idx >= 0:
            self.inc[idx] += val


def solve(operation_names, argument_lists):
    inst = CustomStack(argument_lists[0][0])
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "push":
            inst.push(args[0])
            out.append(None)
        elif op == "pop":
            out.append(inst.pop())
        else:
            inst.increment(args[0], args[1])
            out.append(None)
    return out
