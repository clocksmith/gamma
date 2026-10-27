"""4072. Maximum Alternating Subarray Sum With One Deletion
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-alternating-subarray-sum-with-one-deletion/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4072.Maximum%20Alternating%20Subarray%20Sum%20With%20One%20Deletion/README_EN.md
Complexity: O(n) time, O(1) space.
States track parity of retained subarray length, not original index. Deleting the current element preserves retained parity; keeping it flips parity. Empty subarrays are never admitted. Inputs preserved.
"""

from __future__ import annotations

def solve(nums):
    odd = even = deleted_odd = deleted_even = float('-inf')
    answer = float('-inf')
    for value in nums:
        next_odd = max(value, even+value)
        next_even = odd-value
        next_deleted_odd = max(deleted_even+value, odd)
        next_deleted_even = max(deleted_odd-value, even)
        odd, even = next_odd, next_even
        deleted_odd, deleted_even = next_deleted_odd, next_deleted_even
        answer = max(answer, odd, even, deleted_odd, deleted_even)
    return answer
