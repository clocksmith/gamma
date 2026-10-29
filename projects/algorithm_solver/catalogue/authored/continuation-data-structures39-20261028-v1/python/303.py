"""Original frontend 303 variant; qualification unknown."""


class NumArray:
    def __init__(self, nums):
        prefix = [0] * (len(nums) + 1)
        running = 0
        for i, v in enumerate(nums):
            running += v
            prefix[i + 1] = running
        self.prefix = prefix

    def sumRange(self, left: int, right: int) -> int:
        return self.prefix[right + 1] - self.prefix[left]


def solve(operation_names, argument_lists):
    instance = NumArray(argument_lists[0][0])
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "sumRange":
            out.append(instance.sumRange(args[0], args[1]))
        else:
            raise ValueError("unknown operation")
    return out
