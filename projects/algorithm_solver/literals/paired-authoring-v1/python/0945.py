class Solution:
    def minIncrementForUnique(self, nums: list[int]) -> int:
        nums.sort()
        ordered = nums
        next_free = 0
        moves = 0
        for value in ordered:
            assigned = max(value, next_free)
            moves += assigned - value
            next_free = assigned + 1
        return moves
