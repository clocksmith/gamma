"""465. Optimal Account Balancing. Backtrack over nonzero net balances, merging opposite signs."""

from collections import defaultdict

def solve(transactions: list[list[int]]) -> int:
    balances = defaultdict(int)
    for source, target, amount in transactions:
        balances[source] -= amount
        balances[target] += amount
    remaining = [value for value in balances.values() if value]
    def settle(start):
        while start < len(remaining) and remaining[start] == 0:
            start += 1
        if start == len(remaining):
            return 0
        answer = len(remaining)
        tried = set()
        first = remaining[start]
        for i in range(start + 1, len(remaining)):
            other = remaining[i]
            if first * other >= 0 or other in tried:
                continue
            tried.add(other)
            remaining[i] += first
            answer = min(answer, 1 + settle(start + 1))
            remaining[i] = other
            if other + first == 0:
                break
        return answer
    return settle(0)


class Solution:
    def minTransfers(self, transactions: list[list[int]]) -> int:
        return solve(transactions)
