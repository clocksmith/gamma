"""2086. Minimum Number of Buckets Required to Collect Rainwater from Houses (Medium).

Specification: https://leetcode.com/problems/minimum-number-of-buckets-required-to-collect-rainwater-from-houses/description/
"""


def solve(street: str) -> int:
    cells = list(street)
    n = len(cells)
    count = 0
    for i in range(n):
        if cells[i] != 'H':
            continue
        if (i > 0 and cells[i - 1] == 'B') or (i + 1 < n and cells[i + 1] == 'B'):
            continue
        if i + 1 < n and cells[i + 1] == '.':
            cells[i + 1] = 'B'
            count += 1
        elif i > 0 and cells[i - 1] == '.':
            cells[i - 1] = 'B'
            count += 1
        else:
            return -1
    return count


class Solution:
    def minimumBuckets(self, street: str) -> int:
        return solve(street)
