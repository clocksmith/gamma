class Solution:
    def maximumNumberOfOnes(self, width, height, sideLength, maxOnes):
        weights = []
        for row in range(sideLength):
            row_count = (height + sideLength - 1 - row) // sideLength
            for column in range(sideLength):
                column_count = (width + sideLength - 1 - column) // sideLength
                weights.append(row_count * column_count)
        weights.sort(reverse=True)
        return sum(weights[:maxOnes])
