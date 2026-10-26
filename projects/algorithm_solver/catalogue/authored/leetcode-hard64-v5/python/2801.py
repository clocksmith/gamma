"""2801. Count Stepping Numbers in Range. Rolling digit DP with a separate not-started state."""


def solve(low: str, high: str) -> int:
    """O(110*d) time and O(1) auxiliary space for d decimal digits. Inputs are preserved."""
    modulus = 1_000_000_007

    def through(bound):
        counts = [[0] * 11 for _ in range(2)]
        counts[1][10] = 1
        for char in bound:
            ceiling = ord(char) - 48
            following = [[0] * 11 for _ in range(2)]
            for tight in range(2):
                for previous, ways in enumerate(counts[tight]):
                    if ways == 0:
                        continue
                    for digit in range((ceiling if tight else 9) + 1):
                        next_tight = int(tight == 1 and digit == ceiling)
                        if previous == 10 and digit == 0:
                            next_digit = 10
                        elif previous == 10 or abs(previous - digit) == 1:
                            next_digit = digit
                        else:
                            continue
                        following[next_tight][next_digit] = (following[next_tight][next_digit] + ways) % modulus
            counts = following
        return sum(sum(row[:10]) for row in counts) % modulus

    low_is_stepping = all(abs(ord(low[index]) - ord(low[index - 1])) == 1 for index in range(1, len(low)))
    return (through(high) - through(low) + low_is_stepping) % modulus


class Solution:
    def countSteppingNumbers(self, low: str, high: str) -> int:
        return solve(low, high)
