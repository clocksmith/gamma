"""2217. Find Palindrome With Fixed Length: index the nonzero-leading first half and mirror it without repeating an odd center."""


def solve(queries: list[int], intLength: int) -> list[int]:
    """O(q * L) time and O(q + L) space for q queries and digit length L <= 15; inputs are read-only."""
    half_length = (intLength + 1) // 2
    first = 10 ** (half_length - 1)
    limit = 10 ** half_length
    answer = []
    for query in queries:
        half = first + query - 1
        if half >= limit:
            answer.append(-1)
            continue
        prefix = str(half)
        reflected = prefix[:-1] if intLength % 2 else prefix
        answer.append(int(prefix + reflected[::-1]))
    return answer


class Solution:
    def kthPalindrome(self, queries: list[int], intLength: int) -> list[int]:
        return solve(queries, intLength)
