"""2198. Number of Single Divisor Triplets: enumerate value multisets and count all distinct-index orderings."""


def solve(nums: list[int]) -> int:
    """O(n + u^3) time and O(u) auxiliary space for u <= 100 distinct values; inputs are read-only."""
    counts = {}
    for value in nums:
        counts[value] = counts.get(value, 0) + 1
    values = sorted(counts)
    answer = 0
    for first in range(len(values)):
        a = values[first]
        for second in range(first, len(values)):
            b = values[second]
            for third in range(second, len(values)):
                c = values[third]
                total = a + b + c
                if int(total % a == 0) + int(total % b == 0) + int(total % c == 0) != 1:
                    continue
                if a == b:
                    choices = counts[a] * (counts[a] - 1) // 2 * counts[c]
                elif b == c:
                    choices = counts[a] * (counts[b] * (counts[b] - 1) // 2)
                else:
                    choices = counts[a] * counts[b] * counts[c]
                answer += 6 * choices
    return answer


class Solution:
    def singleDivisorTriplet(self, nums: list[int]) -> int:
        return solve(nums)
