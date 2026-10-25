class Solution:
    def distributeCandies(self, candyType: list[int]) -> int:
        kinds = set(candyType)
        return min(len(kinds), len(candyType) // 2)
