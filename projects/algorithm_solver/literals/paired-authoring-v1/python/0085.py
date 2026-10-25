def histogram_area(heights: list[int]) -> int:
    stack = []
    best = 0
    count = len(heights)
    for right in range(count + 1):
        # A virtual zero flushes the stack without changing heights.
        current = heights[right] if right < count else 0
        start = right
        # Entries have increasing starts and strictly increasing positive heights.
        # Each start is the earliest column supporting that height through right - 1.
        while stack and stack[-1][1] > current:
            left, height = stack.pop()
            best = max(best, height * (right - left))
            start = left
        # Equal heights retain the earlier start instead of adding duplicates.
        if current > 0 and (not stack or stack[-1][1] < current):
            stack.append((start, current))
    return best


class Solution:
    def maximalRectangle(self, matrix: list[list[str]]) -> int:
        if not matrix or not matrix[0]:
            return 0
        columns = len(matrix[0])
        heights = [0] * columns
        best = 0
        for row in matrix:
            for column in range(columns):
                if row[column] == "1":
                    heights[column] += 1
                else:
                    heights[column] = 0
            best = max(best, histogram_area(heights))
        return best
