"""Original frontend 398 variant; qualification unknown."""


class Solution:
    def __init__(self, nums):
        indices = {}
        for i, v in enumerate(nums):
            indices.setdefault(v, []).append(i)
        self.indices = indices
        self._state = 0x9E3779B9

    def _randrange(self, n: int) -> int:
        self._state = (self._state * 1664525 + 1013904223) & 0xFFFFFFFF
        return self._state % n

    def pick(self, target: int) -> int:
        bucket = self.indices[target]
        return bucket[self._randrange(len(bucket))]


def solve(operation_names, argument_lists):
    instance = Solution(argument_lists[0][0])
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "pick":
            out.append(instance.pick(args[0]))
        else:
            raise ValueError("unknown operation")
    return out
