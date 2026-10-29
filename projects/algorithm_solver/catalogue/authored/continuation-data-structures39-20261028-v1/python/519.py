"""Original frontend 519 variant; qualification unknown."""


class Solution:
    def __init__(self, m: int, n: int):
        self.m = int(m)
        self.n = int(n)
        self.total = self.m * self.n
        self.swapped = {}
        self._state = 0x9E3779B9

    def _randrange(self, k: int) -> int:
        self._state = (self._state * 1664525 + 1013904223) & 0xFFFFFFFF
        return self._state % k

    def flip(self):
        r = self._randrange(self.total)
        self.total -= 1
        idx = self.swapped.get(r, r)
        self.swapped[r] = self.swapped.get(self.total, self.total)
        return [idx // self.n, idx % self.n]

    def reset(self) -> None:
        self.total = self.m * self.n
        self.swapped.clear()


def solve(operation_names, argument_lists):
    m, n = argument_lists[0]
    instance = Solution(m, n)
    out = [None]
    for op in operation_names[1:]:
        if op == "flip":
            out.append(instance.flip())
        elif op == "reset":
            instance.reset()
            out.append(None)
        else:
            raise ValueError("unknown operation")
    return out
