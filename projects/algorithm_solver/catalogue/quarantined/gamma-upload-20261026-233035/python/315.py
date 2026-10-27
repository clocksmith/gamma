"""315. Count of Smaller Numbers After Self."""
def solve(nums: list[int]) -> list[int]:
    values = {value: index + 1 for index, value in enumerate(sorted(set(nums)))}
    tree = [0] * (len(values) + 1)
    def add(index):
        while index < len(tree):
            tree[index] += 1
            index += index & -index
    def prefix(index):
        total = 0
        while index:
            total += tree[index]
            index -= index & -index
        return total
    result = []
    for value in reversed(nums):
        index = values[value]
        result.append(prefix(index - 1))
        add(index)
    return result[::-1]

class Solution:
    def countSmaller(self, nums: list[int]) -> list[int]:
        return solve(nums)
