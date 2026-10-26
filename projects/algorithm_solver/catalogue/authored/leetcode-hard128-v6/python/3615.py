"""3615. Longest Palindromic Path in Graph.

Extend palindromic paths at both endpoints using unused equal-label neighbors and subset memoization; O(2^n*n^4) worst-case time and O(2^n*n^2) space. Inputs are preserved.
"""

def solve(n: int, edges: list[list[int]], label: str) -> int:
    adjacent = [0] * n
    labels = [0] * 26
    for node, character in enumerate(label):
        labels[ord(character) - 97] |= 1 << node
    for first, second in edges:
        adjacent[first] |= 1 << second
        adjacent[second] |= 1 << first
    full = (1 << n) - 1
    memo = bytearray((1 << n) * n * n)

    def visit(mask, first, last):
        if first > last:
            first, last = last, first
        identity = (mask * n + first) * n + last
        if memo[identity]:
            return memo[identity]
        best = mask.bit_count()
        upper = n - ((n - best) % 2)
        available = full ^ mask
        left = adjacent[first] & available
        while left:
            bit = left & -left
            left ^= bit
            node = bit.bit_length() - 1
            right = adjacent[last] & available & labels[ord(label[node]) - 97] & ~bit
            while right:
                other_bit = right & -right
                right ^= other_bit
                other = other_bit.bit_length() - 1
                best = max(best, visit(mask | bit | other_bit, node, other))
                if best == upper:
                    memo[identity] = best
                    return best
        memo[identity] = best
        return best

    answer = 1
    for node in range(n):
        answer = max(answer, visit(1 << node, node, node))
    for first, second in edges:
        if label[first] == label[second]:
            answer = max(answer, visit((1 << first) | (1 << second), first, second))
    return answer


class Solution:
    def maxLen(self, n: int, edges: list[list[int]], label: str) -> int:
        return solve(n, edges, label)
