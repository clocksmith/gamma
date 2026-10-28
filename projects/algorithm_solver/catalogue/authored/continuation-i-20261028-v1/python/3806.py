def solve(nums, k, m):
    answer = 0
    for bit in range(30, -1, -1):
        mask = answer | (1 << bit)
        costs = []
        for x in nums:
            missing = mask & ~x
            if not missing:
                costs.append(0)
            else:
                b = missing.bit_length() - 1
                half = 1 << b
                y = (x >> (b + 1) << (b + 1)) + half + (mask & (half - 1))
                costs.append(y - x)
        costs.sort()
        if sum(costs[:m]) <= k:
            answer = mask
    return answer


class Solution:
    def maximumAND(self, nums, k, m):
        return solve(nums, k, m)
