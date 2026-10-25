"""1397. Find All Good Strings."""

def solve(n: int, s1: str, s2: str, evil: str) -> int:
    """KMP automaton plus bounded digit DP: O(26*n*m) time, O(26*m) space."""
    modulus = 1_000_000_007
    size = len(evil)
    pattern = [ord(char) - 97 for char in evil]
    prefix = [0] * size
    for index in range(1, size):
        matched = prefix[index - 1]
        while matched and pattern[index] != pattern[matched]:
            matched = prefix[matched - 1]
        if pattern[index] == pattern[matched]:
            matched += 1
        prefix[index] = matched
    transitions = [[0] * 26 for _ in range(size)]
    for matched in range(size):
        for letter in range(26):
            if letter == pattern[matched]:
                transitions[matched][letter] = matched + 1
            elif matched:
                transitions[matched][letter] = transitions[prefix[matched - 1]][letter]
    # Flags: bit 0 is tight to s1, bit 1 is tight to s2.
    ways = [[0] * 4 for _ in range(size)]
    ways[0][3] = 1
    for position in range(n):
        lower = ord(s1[position]) - 97
        upper = ord(s2[position]) - 97
        following = [[0] * 4 for _ in range(size)]
        for matched in range(size):
            for flags, count in enumerate(ways[matched]):
                if count == 0:
                    continue
                start = lower if flags & 1 else 0
                stop = upper if flags & 2 else 25
                for letter in range(start, stop + 1):
                    next_match = transitions[matched][letter]
                    if next_match == size:
                        continue
                    next_flags = int(bool(flags & 1) and letter == lower)
                    if flags & 2 and letter == upper:
                        next_flags |= 2
                    following[next_match][next_flags] = (
                        following[next_match][next_flags] + count
                    ) % modulus
        ways = following
    return sum(sum(row) for row in ways) % modulus


class Solution:
    def findGoodStrings(self, n: int, s1: str, s2: str, evil: str) -> int:
        return solve(n, s1, s2, evil)
