"""Original frontend 3284 variant; qualification unknown."""

MOD = 10**9 + 7


def solve(nums) -> int:
    def run_dir(step: int) -> int:
        total = 0
        cnt = 0
        cur_sum = 0
        prev = None
        for x in nums:
            if prev is not None and x - prev == step:
                cnt += 1
                cur_sum = (cur_sum + cnt * x) % MOD
            else:
                cnt = 1
                cur_sum = x % MOD
            total = (total + cur_sum) % MOD
            prev = x
        return total

    return (run_dir(1) + run_dir(-1) - sum(nums)) % MOD


getSum = solve


class Solution:
    def getSum(self, nums) -> int:
        return solve(nums)
