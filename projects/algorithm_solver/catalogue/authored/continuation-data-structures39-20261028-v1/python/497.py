"""Original frontend 497 variant; qualification unknown."""


class Solution:
    def __init__(self, rects):
        self.rects = [[a, b, x, y] for a, b, x, y in rects]
        prefix = []
        total = 0
        for a, b, x, y in self.rects:
            total += (x - a + 1) * (y - b + 1)
            prefix.append(total)
        self.prefix = prefix
        self.total = total
        self._state = 0x9E3779B9

    def _randrange(self, n: int) -> int:
        self._state = (self._state * 1664525 + 1013904223) & 0xFFFFFFFF
        return self._state % n

    def pick(self):
        t = self._randrange(self.total)
        low, high = 0, len(self.prefix) - 1
        while low < high:
            mid = (low + high) // 2
            if self.prefix[mid] <= t:
                low = mid + 1
            else:
                high = mid
        idx = low
        base = 0 if idx == 0 else self.prefix[idx - 1]
        offset = t - base
        a, b, x, y = self.rects[idx]
        w = x - a + 1
        return [a + offset % w, b + offset // w]


def solve(operation_names, argument_lists):
    instance = Solution(argument_lists[0][0])
    out = [None]
    for op in operation_names[1:]:
        if op == "pick":
            out.append(instance.pick())
        else:
            raise ValueError("unknown operation")
    return out
