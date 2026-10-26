"""1363. Largest Multiple of Three: remove the fewest smallest digits needed modulo three; O(n) time and O(n) output space."""


def solve(digits: list[int]) -> str:
    counts = [0] * 10
    for digit in digits:
        counts[digit] += 1
    remainder = sum(digits) % 3
    if remainder:
        single = next((digit for digit in range(remainder, 10, 3) if counts[digit]), None)
        if single is not None:
            counts[single] -= 1
        else:
            needed = 2
            for digit in range(3 - remainder, 10, 3):
                take = min(needed, counts[digit])
                counts[digit] -= take
                needed -= take
            if needed:
                return ''
    answer = ''.join(str(digit) * counts[digit] for digit in range(9, -1, -1))
    return '0' if answer and answer[0] == '0' else answer


class Solution:
    def largestMultipleOfThree(self, digits: list[int]) -> str:
        return solve(digits)
