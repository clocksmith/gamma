def solve(nums, target1, target2):
    mod = 1000000007
    even = {0: 1}
    odd = {}
    prefix = 0
    end_odd = end_even = 0
    for x in nums:
        prefix ^= x
        end_odd = even.get(prefix ^ target1, 0)
        end_even = odd.get(prefix ^ target2, 0)
        odd[prefix] = (odd.get(prefix, 0) + end_odd) % mod
        even[prefix] = (even.get(prefix, 0) + end_even) % mod
    return (end_odd + end_even) % mod


class Solution:
    def alternatingXOR(self, nums, target1, target2):
        return solve(nums, target1, target2)
