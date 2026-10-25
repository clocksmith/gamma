class Solution:
    def spiralOrder(self, matrix: list[list[int]]) -> list[int]:
        if not matrix or not matrix[0]:
            return []

        result = []
        top = 0
        bottom = len(matrix) - 1
        left = 0
        right = len(matrix[0]) - 1
        while top <= bottom and left <= right:
            for column in range(left, right + 1):
                result.append(matrix[top][column])
            top += 1
            for row in range(top, bottom + 1):
                result.append(matrix[row][right])
            right -= 1
            if top <= bottom:
                for column in range(right, left - 1, -1):
                    result.append(matrix[bottom][column])
                bottom -= 1
            if left <= right:
                for row in range(bottom, top - 1, -1):
                    result.append(matrix[row][left])
                left += 1
        return result
