def visible_ahead(heights: list[int]) -> list[int]:
    output = [0] * len(heights)
    stack = []
    for index in range(len(heights) - 1, -1, -1):
        height = heights[index]
        while stack and stack[-1] < height:
            stack.pop()
            output[index] += 1
        if stack:
            output[index] += 1
            if stack[-1] == height:
                stack.pop()
        stack.append(height)
    return output


class Solution:
    def seePeople(self, heights: list[list[int]]) -> list[list[int]]:
        rows = len(heights)
        columns = len(heights[0]) if rows > 0 else 0
        output = [visible_ahead(row) for row in heights]
        for column in range(columns):
            column_heights = [heights[row][column] for row in range(rows)]
            counts = visible_ahead(column_heights)
            for row in range(rows):
                output[row][column] += counts[row]
        return output
