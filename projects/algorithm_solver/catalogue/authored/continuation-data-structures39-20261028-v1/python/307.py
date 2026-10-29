"""Original frontend 307 variant; qualification unknown."""


class NumArray:
    def __init__(self, nums):
        n = len(nums)
        self.n = n
        self.vals = list(nums)
        tree = [0] + list(nums)
        for i in range(1, n + 1):
            j = i + (i & -i)
            if j <= n:
                tree[j] += tree[i]
        self.tree = tree

    def update(self, index: int, val: int) -> None:
        delta = val - self.vals[index]
        self.vals[index] = val
        i = index + 1
        n = self.n
        tree = self.tree
        while i <= n:
            tree[i] += delta
            i += i & -i

    def _prefix(self, i: int) -> int:
        s = 0
        tree = self.tree
        while i > 0:
            s += tree[i]
            i -= i & -i
        return s

    def sumRange(self, left: int, right: int) -> int:
        return self._prefix(right + 1) - self._prefix(left)


def solve(operation_names, argument_lists):
    instance = NumArray(argument_lists[0][0])
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "update":
            instance.update(args[0], args[1])
            out.append(None)
        elif op == "sumRange":
            out.append(instance.sumRange(args[0], args[1]))
        else:
            raise ValueError("unknown operation")
    return out
