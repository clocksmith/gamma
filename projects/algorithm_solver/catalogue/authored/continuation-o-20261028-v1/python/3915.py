"""Original frontend 3915 variant; qualification unknown."""

def solve(nums, k):
    ordered = sorted(set(nums))
    ranks = {value: i + 1 for i, value in enumerate(ordered)}
    size = len(ordered)
    low, high = [0] * (size + 1), [0] * (size + 1)
    def update(tree, index, value):
        while index <= size:
            tree[index] = max(tree[index], value)
            index += index & -index
    def query(tree, index):
        value = 0
        while index:
            value = max(value, tree[index])
            index -= index & -index
        return value
    up, down = [0] * len(nums), [0] * len(nums)
    answer = 0
    for i, value in enumerate(nums):
        if i >= k:
            j = i - k
            update(low, ranks[nums[j]], down[j])
            update(high, size + 1 - ranks[nums[j]], up[j])
        rank = ranks[value]
        up[i] = value + query(low, rank - 1)
        down[i] = value + query(high, size - rank)
        answer = max(answer, up[i], down[i])
    return answer


class Solution:
    def maxAlternatingSum(self, nums, k):
        return solve(nums, k)
