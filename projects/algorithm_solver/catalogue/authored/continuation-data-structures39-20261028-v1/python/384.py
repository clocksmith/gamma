"""Original frontend 384 variant; qualification unknown."""


class Solution:
    def __init__(self, nums):
        self.orig = list(nums)
        self._state = 0x9E3779B9

    def _randrange(self, n: int) -> int:
        self._state = (self._state * 1664525 + 1013904223) & 0xFFFFFFFF
        return self._state % n

    def reset(self):
        return list(self.orig)

    def shuffle(self):
        arr = list(self.orig)
        for i in range(len(arr) - 1, 0, -1):
            j = self._randrange(i + 1)
            arr[i], arr[j] = arr[j], arr[i]
        return arr


def solve(operation_names, argument_lists):
    instance = Solution(argument_lists[0][0])
    out = [None]
    for op in operation_names[1:]:
        if op == "reset":
            out.append(instance.reset())
        elif op == "shuffle":
            out.append(instance.shuffle())
        else:
            raise ValueError("unknown operation")
    return out
