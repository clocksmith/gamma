"""491. Non-decreasing Subsequences."""

def solve(nums: list[int]) -> list[list[int]]:
    answer, path = [], []
    def search(start):
        if len(path) >= 2:
            answer.append(path[:])
        used = set()
        for i in range(start, len(nums)):
            value = nums[i]
            if value in used or path and value < path[-1]:
                continue
            used.add(value)
            path.append(value)
            search(i + 1)
            path.pop()
    search(0)
    return answer


class Solution:
    def findSubsequences(self, nums: list[int]) -> list[list[int]]:
        return solve(nums)
