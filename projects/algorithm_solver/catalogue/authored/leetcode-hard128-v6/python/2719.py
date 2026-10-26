"""2719. Count of Integers.

Bounded decimal digit-sum dynamic programming, subtracting the lower exclusive prefix; O(L*min(9L,max_sum)*10) time and O(min(9L,max_sum)) space. Inputs are preserved.
"""

def solve(num1: str, num2: str, min_sum: int, max_sum: int) -> int:
    modulus = 1_000_000_007

    def count_through(bound):
        if bound < 0:
            return 0
        digits = str(bound)
        cap = min(max_sum, 9 * len(digits))
        loose = [0] * (cap + 1)
        tight_sum = 0
        for character in digits:
            digit = int(character)
            following = [0] * (cap + 1)
            for total, ways in enumerate(loose):
                if ways:
                    for value in range(min(9, cap - total) + 1):
                        following[total + value] = (following[total + value] + ways) % modulus
            for value in range(digit):
                if tight_sum + value <= cap:
                    following[tight_sum + value] = (following[tight_sum + value] + 1) % modulus
            tight_sum += digit
            loose = following
        return (sum(loose[min_sum:]) + int(min_sum <= tight_sum <= max_sum)) % modulus

    return (count_through(int(num2)) - count_through(int(num1) - 1)) % modulus


class Solution:
    def count(self, num1: str, num2: str, min_sum: int, max_sum: int) -> int:
        return solve(num1, num2, min_sum, max_sum)
