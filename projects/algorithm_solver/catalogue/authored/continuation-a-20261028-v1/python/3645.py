from collections import defaultdict

def solve(value, limit):
    groups = defaultdict(list)
    for amount, threshold in zip(value, limit):
        groups[threshold].append(amount)
    return sum(sum(sorted(amounts, reverse=True)[:threshold]) for threshold, amounts in groups.items())


class Solution:
    def maxTotal(self, value, limit):
        return solve(value, limit)
