"""Original frontend 3748 development candidate; qualification unknown."""

def solve(nums, queries):
    from bisect import bisect_right
    n = len(nums)
    ends = [n - 1] * n
    for i in range(n - 2, -1, -1):
        ends[i] = ends[i + 1] if nums[i] <= nums[i + 1] else i
    prefix = [0]
    for i in range(n):
        prefix.append(prefix[-1] + ends[i] - i + 1)
    answer = []
    for left, right in queries:
        split = bisect_right(ends, right, left, right + 1)
        length = right - split + 1
        answer.append(prefix[split] - prefix[left] + length * (length + 1) // 2)
    return answer


class Solution:
    def countStableSubarrays(self, nums, queries):
        return solve(nums, queries)
