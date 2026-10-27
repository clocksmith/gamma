"""307. Range Sum Query - Mutable."""
class NumArray:
    def __init__(self, nums: list[int]):
        self.values = nums[:]
        self.tree = [0] * (len(nums) + 1)
        for index, value in enumerate(nums):
            self._add(index + 1, value)

    def _add(self, index: int, difference: int) -> None:
        while index < len(self.tree):
            self.tree[index] += difference
            index += index & -index

    def update(self, index: int, val: int) -> None:
        difference = val - self.values[index]
        self.values[index] = val
        self._add(index + 1, difference)

    def _prefix(self, index: int) -> int:
        total = 0
        while index:
            total += self.tree[index]
            index -= index & -index
        return total

    def sumRange(self, left: int, right: int) -> int:
        return self._prefix(right + 1) - self._prefix(left)

def solve(nums: list[int], operations: list[str], arguments: list[list[int]]) -> list:
    structure = NumArray(nums)
    return [getattr(structure, operation)(*values) for operation, values in zip(operations, arguments)]
