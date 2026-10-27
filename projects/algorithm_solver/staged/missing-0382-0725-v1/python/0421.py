"""421. Maximum XOR of Two Numbers in an Array. Build the answer from high bits using complementary prefixes."""

def solve(nums: list[int]) -> int:
    answer = mask = 0
    for bit in range(30, -1, -1):
        mask |= 1 << bit
        prefixes = {value & mask for value in nums}
        candidate = answer | (1 << bit)
        if any((candidate ^ prefix) in prefixes for prefix in prefixes):
            answer = candidate
    return answer


class Solution:
    def findMaximumXOR(self, nums: list[int]) -> int:
        return solve(nums)
