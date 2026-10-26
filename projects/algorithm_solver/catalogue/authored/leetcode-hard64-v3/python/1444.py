"""1444. Number of Ways of Cutting a Pizza: suffix apple counts and cut DP; O(k*rows*columns*(rows+columns)) time and O(rows*columns) space."""


def solve(pizza: list[str], k: int) -> int:
    modulus = 1_000_000_007
    rows, columns = len(pizza), len(pizza[0])
    apples = [[0] * (columns + 1) for _ in range(rows + 1)]
    for row in range(rows - 1, -1, -1):
        for column in range(columns - 1, -1, -1):
            apples[row][column] = (int(pizza[row][column] == 'A') + apples[row + 1][column]
                                    + apples[row][column + 1] - apples[row + 1][column + 1])
    previous = [[int(apples[row][column] > 0) for column in range(columns)] for row in range(rows)]
    for _ in range(2, k + 1):
        current = [[0] * columns for _ in range(rows)]
        for row in range(rows):
            for column in range(columns):
                for cut in range(row + 1, rows):
                    if apples[row][column] > apples[cut][column]:
                        current[row][column] = (current[row][column] + previous[cut][column]) % modulus
                for cut in range(column + 1, columns):
                    if apples[row][column] > apples[row][cut]:
                        current[row][column] = (current[row][column] + previous[row][cut]) % modulus
        previous = current
    return previous[0][0]


class Solution:
    def ways(self, pizza: list[str], k: int) -> int:
        return solve(pizza, k)
