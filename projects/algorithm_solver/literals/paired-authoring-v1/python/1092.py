class Solution:
    def shortestCommonSupersequence(self, str1: str, str2: str) -> str:
        rows = len(str1)
        columns = len(str2)
        common = [[0] * (columns + 1) for _ in range(rows + 1)]
        for row in range(1, rows + 1):
            for column in range(1, columns + 1):
                if str1[row - 1] == str2[column - 1]:
                    common[row][column] = common[row - 1][column - 1] + 1
                else:
                    common[row][column] = max(common[row - 1][column], common[row][column - 1])
        result = []
        row = rows
        column = columns
        while row or column:
            if row == 0:
                column -= 1
                result.append(str2[column])
            elif column == 0 or common[row][column] == common[row - 1][column]:
                row -= 1
                result.append(str1[row])
            elif common[row][column] == common[row][column - 1]:
                column -= 1
                result.append(str2[column])
            else:
                row -= 1
                column -= 1
                result.append(str1[row])
        result.reverse()
        return "".join(result)
