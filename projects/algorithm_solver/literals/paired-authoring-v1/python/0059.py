class Solution:
    def generateMatrix(self, n: int) -> list[list[int]]:
        matrix = [[0] * n for _ in range(n)]
        top = 0
        bottom = n - 1
        left = 0
        right = n - 1
        value = 1
        while top <= bottom and left <= right:
            for column in range(left, right + 1):
                matrix[top][column] = value
                value += 1
            top += 1
            for row in range(top, bottom + 1):
                matrix[row][right] = value
                value += 1
            right -= 1
            if top <= bottom:
                for column in range(right, left - 1, -1):
                    matrix[bottom][column] = value
                    value += 1
                bottom -= 1
            if left <= right:
                for row in range(bottom, top - 1, -1):
                    matrix[row][left] = value
                    value += 1
                left += 1
        return matrix
