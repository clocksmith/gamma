"""1830. Minimum Number of Operations to Make String Sorted: multiset lexicographic rank modulo a prime."""


def solve(s: str) -> int:
    """O(26*n + log MOD) time and O(n) auxiliary space. Inputs are preserved."""
    modulus = 1_000_000_007
    length = len(s)
    factorial = [1] * (length + 1)
    for index in range(1, length + 1):
        factorial[index] = factorial[index - 1] * index % modulus
    inverse = [1] * (length + 1)
    inverse[length] = pow(factorial[length], modulus - 2, modulus)
    for index in range(length, 0, -1):
        inverse[index - 1] = inverse[index] * index % modulus
    counts = [0] * 26
    for character in s:
        counts[ord(character) - 97] += 1
    denominator_inverse = 1
    for count in counts:
        denominator_inverse = denominator_inverse * inverse[count] % modulus
    answer = 0
    for position, character in enumerate(s):
        index = ord(character) - 97
        smaller = sum(counts[:index])
        answer = (answer + smaller * factorial[length - position - 1] * denominator_inverse) % modulus
        denominator_inverse = denominator_inverse * counts[index] % modulus
        counts[index] -= 1
    return answer


class Solution:
    def makeStringSorted(self, s: str) -> int:
        return solve(s)
