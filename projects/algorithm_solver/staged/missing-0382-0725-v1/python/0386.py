"""386. Lexicographical Numbers. Iterative decimal trie traversal; O(n) time."""

def solve(n: int) -> list[int]:
    answer = []
    value = 1
    for _ in range(n):
        answer.append(value)
        if value * 10 <= n:
            value *= 10
        else:
            while value % 10 == 9 or value + 1 > n:
                value //= 10
            value += 1
    return answer


class Solution:
    def lexicalOrder(self, n: int) -> list[int]:
        return solve(n)
