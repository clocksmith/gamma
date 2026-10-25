class Solution:
    def heightChecker(self, heights: list[int]) -> int:
        expected = sorted(heights)
        mismatches = 0
        for index in range(len(heights)):
            if heights[index] != expected[index]:
                mismatches += 1
        return mismatches
