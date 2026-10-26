"""3448. Count Substrings Divisible By Last Digit.

Maintain suffix remainder counts independently for divisors one through nine; O(45*n) time and O(45) working space. Input is preserved.
"""

def solve(s: str) -> int:
    counts = [[]] + [[0] * divisor for divisor in range(1, 10)]
    answer = 0
    for character in s:
        digit = int(character)
        for divisor in range(1, 10):
            following = [0] * divisor
            following[digit % divisor] = 1
            for remainder, count in enumerate(counts[divisor]):
                following[(10 * remainder + digit) % divisor] += count
            counts[divisor] = following
        if digit:
            answer += counts[digit][0]
    return answer


class Solution:
    def countSubstrings(self, s: str) -> int:
        return solve(s)
