"""1259. Handshakes That Do Not Cross.

Catalan interval decomposition; O(n^2) time and O(n) space for n pairs.
"""

def solve(numPeople: int) -> int:
    modulus = 1_000_000_007
    pairs = numPeople // 2
    ways = [1] + [0] * pairs
    for size in range(1, pairs + 1):
        ways[size] = sum(ways[left] * ways[size - left - 1] for left in range(size)) % modulus
    return ways[pairs]


class Solution:
    def numberOfWays(self, numPeople: int) -> int:
        return solve(numPeople)
