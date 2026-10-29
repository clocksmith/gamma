# 315 — Count of Smaller Numbers After Self. Original implementation; authored candidate, not independently qualified.
def solve(nums):
    ranks = {value: i + 1 for i, value in enumerate(sorted(set(nums)))}
    bit = [0] * (len(ranks) + 1)
    result = [0] * len(nums)
    for i in range(len(nums) - 1, -1, -1):
        rank = ranks[nums[i]]
        j = rank - 1
        while j:
            result[i] += bit[j]
            j -= j & -j
        j = rank
        while j < len(bit):
            bit[j] += 1
            j += j & -j
    return result

countSmaller = solve

class Solution:
    countSmaller = staticmethod(solve)
