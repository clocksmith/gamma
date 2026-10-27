"""321. Create Maximum Number."""
def best_subsequence(nums: list[int], length: int) -> list[int]:
    remove = len(nums) - length
    stack = []
    for value in nums:
        while remove and stack and stack[-1] < value:
            stack.pop()
            remove -= 1
        stack.append(value)
    return stack[:length]

def merge(left: list[int], right: list[int]) -> list[int]:
    result = []
    while left or right:
        if left > right:
            result.append(left.pop(0))
        else:
            result.append(right.pop(0))
    return result

def solve(nums1: list[int], nums2: list[int], k: int) -> list[int]:
    best = []
    for left_length in range(max(0, k - len(nums2)), min(k, len(nums1)) + 1):
        candidate = merge(best_subsequence(nums1, left_length), best_subsequence(nums2, k - left_length))
        best = max(best, candidate)
    return best

class Solution:
    def maxNumber(self, nums1, nums2, k):
        return solve(nums1, nums2, k)
