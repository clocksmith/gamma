class Solution:
    def maxProduct(self, nums: list[int]) -> int:
        largest = 0
        second = 0
        for value in nums:
            if value >= largest:
                second = largest
                largest = value
            elif value > second:
                second = value
        return (largest - 1) * (second - 1)
