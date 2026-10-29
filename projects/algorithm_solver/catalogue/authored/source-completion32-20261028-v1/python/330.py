# 330 — Patching Array. Original implementation; authored candidate, not independently qualified.
def solve(nums, n):
    # Every value in [1, missing) is representable by processed elements.
    missing, i, patches = 1, 0, 0
    while missing <= n:
        if i < len(nums) and nums[i] <= missing:
            missing += nums[i]
            i += 1
        else:
            missing *= 2
            patches += 1
    return patches

minPatches = solve

class Solution:
    minPatches = staticmethod(solve)
