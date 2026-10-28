"""2483. Minimum Penalty for a Shop (Medium).

Specification: https://leetcode.com/problems/minimum-penalty-for-a-shop/description/
"""


def solve(customers):
    total_y = customers.count('Y')
    prefix_n, suffix_y, best, best_pen = 0, total_y, 0, float('inf')
    for j in range(len(customers) + 1):
        pen = prefix_n + suffix_y
        if pen < best_pen:
            best_pen, best = pen, j
        if j < len(customers):
            if customers[j] == 'N':
                prefix_n += 1
            else:
                suffix_y -= 1
    return best


class Solution:
    def bestClosingTime(self, customers):
        return solve(customers)
