"""Original frontend 799 variant; qualification not qualified."""

def solve(poured, query_row, query_glass):
    row = [float(poured)]
    for r in range(query_row):
        following = [0.0] * (r + 2)
        for c, amount in enumerate(row):
            if amount > 1.0:
                half = (amount - 1.0) / 2.0
                following[c] += half
                following[c + 1] += half
        row = following
    return min(1.0, row[query_glass])


class Solution:
    def champagneTower(self, poured, query_row, query_glass):
        return solve(poured, query_row, query_glass)
