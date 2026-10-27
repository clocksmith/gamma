"""666. Path Sum IV."""

def solve(nums: list[int]) -> int:
    values = {number // 10: number % 10 for number in nums}
    answer = 0
    stack = [(11, 0)]
    while stack:
        key, total = stack.pop()
        total += values[key]
        depth, position = divmod(key, 10)
        left = (depth + 1) * 10 + 2 * position - 1
        right = left + 1
        if left not in values and right not in values:
            answer += total
        if left in values:
            stack.append((left, total))
        if right in values:
            stack.append((right, total))
    return answer


class Solution:
    def pathSum(self, nums: list[int]) -> int:
        return solve(nums)
