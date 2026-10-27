"""483. Smallest Good Base. Search digit counts and bases using exact geometric-series comparisons."""

def solve(n: str) -> str:
    number = int(n)
    for exponent in range(number.bit_length() - 1, 1, -1):
        low = 2
        high = min(number - 1, 1 << ((number.bit_length() + exponent - 1) // exponent))
        while low <= high:
            base = (low + high) // 2
            total = 1
            for _ in range(exponent):
                total = total * base + 1
                if total > number:
                    break
            if total == number:
                return str(base)
            if total < number:
                low = base + 1
            else:
                high = base - 1
    return str(number - 1)


class Solution:
    def smallestGoodBase(self, n: str) -> str:
        return solve(n)
