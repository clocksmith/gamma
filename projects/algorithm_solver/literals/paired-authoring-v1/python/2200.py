class Solution:
    def findKDistantIndices(self, nums: list[int], key: int, k: int) -> list[int]:
        output = []
        next_index = 0
        for index, value in enumerate(nums):
            if value == key:
                left = max(next_index, index - k)
                right = min(len(nums) - 1, index + k)
                for position in range(left, right + 1):
                    output.append(position)
                next_index = right + 1
        return output
