"""303. Range Sum Query - Immutable."""
class NumArray:
    def __init__(self, nums: list[int]):
        self.prefix = [0]
        for value in nums:
            self.prefix.append(self.prefix[-1] + value)

    def sumRange(self, left: int, right: int) -> int:
        return self.prefix[right + 1] - self.prefix[left]

def solve(nums: list[int], queries: list[list[int]]) -> list[int]:
    array = NumArray(nums)
    return [array.sumRange(*query) for query in queries]
