class Solution:
    def triangleNumber(self, nums: list[int]) -> int:
        ordered = sorted(nums)
        count = 0
        for largest in range(len(ordered) - 1, 1, -1):
            left = 0
            right = largest - 1
            while left < right:
                if ordered[left] + ordered[right] > ordered[largest]:
                    count += right - left
                    right -= 1
                else:
                    left += 1
        return count
