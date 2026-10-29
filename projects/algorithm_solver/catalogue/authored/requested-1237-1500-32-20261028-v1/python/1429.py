"""Original frontend 1429 variant; qualification unknown."""


class FirstUnique:
    def __init__(self, nums):
        self.unique = {}
        self.seen = set()
        for v in nums:
            self.add(v)

    def showFirstUnique(self) -> int:
        if not self.unique:
            return -1
        return next(iter(self.unique))

    def add(self, value: int) -> None:
        if value not in self.seen:
            self.seen.add(value)
            self.unique[value] = True
        else:
            self.unique.pop(value, None)


def solve(operation_names, argument_lists):
    inst = FirstUnique(argument_lists[0][0])
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "add":
            inst.add(args[0])
            out.append(None)
        else:
            out.append(inst.showFirstUnique())
    return out
