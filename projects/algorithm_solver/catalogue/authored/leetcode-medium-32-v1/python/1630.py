"""1630. Arithmetic Subarrays: check unique positions in the implied arithmetic progression."""


def solve(nums: list[int], l: list[int], r: list[int]) -> list[bool]:
    """O(total queried length) expected time and O(longest query length) auxiliary space; inputs are read-only."""
    answer = []
    for left, right in zip(l, r):
        low = high = nums[left]
        for index in range(left + 1, right + 1):
            low = min(low, nums[index])
            high = max(high, nums[index])
        if low == high:
            answer.append(True)
            continue
        gaps = right - left
        if (high - low) % gaps:
            answer.append(False)
            continue
        step = (high - low) // gaps
        seen = set()
        valid = True
        for index in range(left, right + 1):
            value = nums[index]
            if (value - low) % step or value in seen:
                valid = False
                break
            seen.add(value)
        answer.append(valid)
    return answer


class Solution:
    def checkArithmeticSubarrays(self, nums: list[int], l: list[int], r: list[int]) -> list[bool]:
        return solve(nums, l, r)
