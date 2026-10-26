"""1220. Count Vowels Permutation.

Five-state transition DP; O(n) time and O(1) space.
"""

def solve(n: int) -> int:
    modulus = 1_000_000_007
    a = e = i = o = u = 1
    for _ in range(1, n):
        a, e, i, o, u = (e + i + u) % modulus, (a + i) % modulus, (e + o) % modulus, i, (i + o) % modulus
    return (a + e + i + o + u) % modulus


class Solution:
    def countVowelPermutation(self, n: int) -> int:
        return solve(n)
