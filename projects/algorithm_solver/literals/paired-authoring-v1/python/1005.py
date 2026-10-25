class Solution:
    def largestSumAfterKNegations(self, nums, k):
        ordered = sorted(nums)
        for index in range(len(ordered)):
            if k == 0 or ordered[index] >= 0:
                break
            ordered[index] = -ordered[index]
            k -= 1
        total = 0
        smallest = abs(ordered[0])
        for value in ordered:
            total += value
            smallest = min(smallest, abs(value))
        if k % 2 == 1:
            total -= 2 * smallest
        return total
