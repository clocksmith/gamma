"""477. Total Hamming Distance."""

def solve(nums: list[int]) -> int:
    answer = 0
    for bit in range(31):
        ones = sum((value >> bit) & 1 for value in nums)
        answer += ones * (len(nums) - ones)
    return answer


class Solution:
    def totalHammingDistance(self, nums: list[int]) -> int:
        return solve(nums)
