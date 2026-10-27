"""3874. Valid Subarrays With Exactly One Peak
Authored candidate: not executed, imported, syntax-checked, tested, or qualified.
Signature: solve(nums, k).
Algorithm: Count legal left/right endpoint choices around each original-array peak, excluding neighboring peaks.
Complexity: O(n) time; O(n) space.
Numeric semantics: Exact integer arithmetic on the published input bounds; JavaScript Number results remain safe integers.
Mutation: Does not mutate input arrays, rows, strings, or trees.
Interface: Ordered-positional solve; native forwarding name included only when confirmed.
Specification: https://leetcode.com/problems/valid-subarrays-with-exactly-one-peak/description/
Consulted public statement/reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3874.Valid%20Subarrays%20With%20Exactly%20One%20Peak/README_EN.md
Reference repository attribution: Doocs contributors, CC-BY-SA-4.0.
New readable implementations; no third-party source bodies copied verbatim.
No protected tests or private reference implementations used.
Contract note: Peak status is determined in nums, not recomputed within a subarray. A singleton containing a peak is valid.
"""

def solve(nums, k):
    size = len(nums)
    peaks = [index for index in range(1, size - 1)
             if nums[index] > nums[index - 1] and nums[index] > nums[index + 1]]
    total = 0
    for offset, peak in enumerate(peaks):
        previous = peaks[offset - 1] if offset else -1
        following = peaks[offset + 1] if offset + 1 < len(peaks) else size
        left = max(0, peak - k, previous + 1)
        right = min(size - 1, peak + k, following - 1)
        total += (peak - left + 1) * (right - peak + 1)
    return total


def validSubarrays(nums, k):
    return solve(nums, k)


class Solution:
    def validSubarrays(self, nums, k):
        return solve(nums, k)
