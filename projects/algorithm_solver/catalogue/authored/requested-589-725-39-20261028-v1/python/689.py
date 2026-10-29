"""Original LeetCode 689 candidate; qualification unknown."""

def solve(nums, k):
    windows, total = [], sum(nums[:k])
    windows.append(total)
    for i in range(k, len(nums)):
        total += nums[i] - nums[i-k]
        windows.append(total)
    size = len(windows)
    left, right = [0] * size, [size-1] * size
    best = 0
    for i in range(size):
        if windows[i] > windows[best]: best = i
        left[i] = best
    best = size - 1
    for i in range(size - 1, -1, -1):
        if windows[i] >= windows[best]: best = i
        right[i] = best
    answer, best_total = None, -1
    for middle in range(k, size-k):
        a, c = left[middle-k], right[middle+k]
        candidate = [a, middle, c]
        value = windows[a] + windows[middle] + windows[c]
        if value > best_total:
            best_total, answer = value, candidate
    return answer


class Solution:
    def maxSumOfThreeSubarrays(self, nums, k):
        return solve(nums, k)
