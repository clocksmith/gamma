"""3272. Find the Count of Good Integers.

Enumerate divisible palindromes, deduplicate digit multisets, and count permutations excluding leading zero; O(n*10^ceil(n/2)) time and space proportional to distinct multisets. Inputs are preserved.
"""

from math import factorial


def solve(n: int, k: int) -> int:
    half = (n + 1) // 2
    seen = set()
    answer = 0
    for prefix in range(10 ** (half - 1), 10 ** half):
        left = str(prefix)
        text = left + (left[:-1] if n % 2 else left)[::-1]
        if int(text) % k:
            continue
        counts = [0] * 10
        for character in text:
            counts[int(character)] += 1
        identity = tuple(counts)
        if identity in seen:
            continue
        seen.add(identity)
        denominator = 1
        for count in counts:
            denominator *= factorial(count)
        answer += (n - counts[0]) * factorial(n - 1) // denominator
    return answer


class Solution:
    def countGoodIntegers(self, n: int, k: int) -> int:
        return solve(n, k)
