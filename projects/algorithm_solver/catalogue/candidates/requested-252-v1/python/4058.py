"""4058. Maximum Pulse Value After One Subarray Rotation
Candidate source; not executed, syntax-checked, tested, or qualified.
Specification: https://leetcode.com/problems/maximum-pulse-value-after-one-subarray-rotation/description/
Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4058.Maximum%20Pulse%20Value%20After%20One%20Subarray%20Rotation/README_EN.md
Complexity: O(n) time, O(1) space.
For [l,r], gain = -2*P[r+1]+2*P[l]+(sign(l)+sign(r))*nums[l]. Two parity-specific maxima cover all earlier l. Evaluate before inserting l=r, enforcing l<r. No-operation gain zero is retained. Inputs preserved.
"""

from __future__ import annotations

def solve(nums):
    prefix = 0
    gain = 0
    best = [float('-inf'), float('-inf')]
    for index, value in enumerate(nums):
        sign = 1 if index % 2 == 0 else -1
        before = prefix
        prefix += sign*value
        gain = max(gain, best[index % 2]-2*prefix)
        # Store the contribution of this left endpoint for a future right endpoint.
        best[0] = max(best[0], 2*before+(sign+1)*value)
        best[1] = max(best[1], 2*before+(sign-1)*value)
    return prefix+gain
