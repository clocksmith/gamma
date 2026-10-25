class Solution:
    def shortestCommonSupersequence(self, str1: str, str2: str) -> str:
        rows = len(str1)
        columns = len(str2)
        lengths = [[0] * (columns + 1) for _ in range(rows + 1)]
        for row in range(rows + 1):
            lengths[row][columns] = rows - row
        for column in range(columns + 1):
            lengths[rows][column] = columns - column
        for row in range(rows - 1, -1, -1):
            for column in range(columns - 1, -1, -1):
                if str1[row] == str2[column]:
                    lengths[row][column] = 1 + lengths[row + 1][column + 1]
                else:
                    lengths[row][column] = 1 + min(lengths[row + 1][column], lengths[row][column + 1])
        result = []
        row = 0
        column = 0
        while row < rows and column < columns:
            if str1[row] == str2[column]:
                result.append(str1[row])
                row += 1
                column += 1
            elif lengths[row + 1][column] <= lengths[row][column + 1]:
                result.append(str1[row])
                row += 1
            else:
                result.append(str2[column])
                column += 1
        while row < rows:
            result.append(str1[row])
            row += 1
        while column < columns:
            result.append(str2[column])
            column += 1
        return "".join(result)
