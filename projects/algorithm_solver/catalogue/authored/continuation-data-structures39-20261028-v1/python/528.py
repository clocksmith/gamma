"""Original frontend 528 variant; qualification unknown."""


class Solution:
    def __init__(self, w):
        prefix = []
        total = 0
        for v in w:
            total += v
            prefix.append(total)
        self.prefix = prefix
        self.total = total
        self._state = 0x9E3779B9

    def _randrange(self, n: int) -> int:
        self._state = (self._state * 1664525 + 1013904223) & 0xFFFFFFFF
        return self._state % n

    def pickIndex(self) -> int:
        target = self._randrange(self.total) + 1
        low, high = 0, len(self.prefix) - 1
        while low < high:
            mid = (low + high) // 2
            if self.prefix[mid] < target:
                low = mid + 1
            else:
                high = mid
        return low


def solve(operation_names, argument_lists):
    instance = Solution(argument_lists[0][0])
    out = [None]
    for op in operation_names[1:]:
        if op == "pickIndex":
            out.append(instance.pickIndex())
        else:
            raise ValueError("unknown operation")
    return out
