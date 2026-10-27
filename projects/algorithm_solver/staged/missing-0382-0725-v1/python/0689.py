"""689. Maximum Sum of 3 Non-Overlapping Subarrays. Best left/right windows enforce non-overlap and lexicographic tie-breaking."""

def solve(nums: list[int], k: int) -> list[int]:
    windows = []
    total = sum(nums[:k])
    windows.append(total)
    for i in range(k, len(nums)):
        total += nums[i] - nums[i - k]
        windows.append(total)
    size = len(windows)
    left = [0] * size
    right = [0] * size
    best = 0
    for i in range(size):
        if windows[i] > windows[best]:
            best = i
        left[i] = best
    best = size - 1
    for i in range(size - 1, -1, -1):
        if windows[i] >= windows[best]:
            best = i
        right[i] = best
    answer = None
    maximum = float('-inf')
    for middle in range(k, size - k):
        a, c = left[middle - k], right[middle + k]
        score = windows[a] + windows[middle] + windows[c]
        candidate = [a, middle, c]
        if score > maximum or score == maximum and (answer is None or candidate < answer):
            maximum, answer = score, candidate
    return answer


class Solution:
    def maxSumOfThreeSubarrays(self, nums: list[int], k: int) -> list[int]:
        return solve(nums, k)
