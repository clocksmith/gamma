"""Original frontend 1476 variant; qualification unknown."""


class SubrectangleQueries:
    def __init__(self, rectangle):
        self.base = [list(r) for r in rectangle]
        self.ops = []

    def updateSubrectangle(self, row1: int, col1: int, row2: int, col2: int, newValue: int) -> None:
        self.ops.append((row1, col1, row2, col2, newValue))

    def getValue(self, row: int, col: int) -> int:
        for r1, c1, r2, c2, v in reversed(self.ops):
            if r1 <= row <= r2 and c1 <= col <= c2:
                return v
        return self.base[row][col]


def solve(operation_names, argument_lists):
    inst = SubrectangleQueries(argument_lists[0][0])
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "updateSubrectangle":
            inst.updateSubrectangle(args[0], args[1], args[2], args[3], args[4])
            out.append(None)
        else:
            out.append(inst.getValue(args[0], args[1]))
    return out
