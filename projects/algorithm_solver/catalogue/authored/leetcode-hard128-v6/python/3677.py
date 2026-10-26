"""3677. Count Binary Palindromic Numbers.

Count shorter palindrome lengths and unrank the leading half at the bound length, including zero; O(log n) arithmetic operations and space. Inputs are preserved.
"""

def solve(n: int) -> int:
    if n == 0:
        return 1
    bits = bin(n)[2:]
    length = len(bits)
    answer = 1
    for size in range(1, length):
        answer += 1 << ((size + 1) // 2 - 1)
    half = (length + 1) // 2
    prefix = bits[:half]
    answer += int(prefix, 2) - (1 << (half - 1))
    reflected = prefix[:-1] if length % 2 else prefix
    palindrome = int(prefix + reflected[::-1], 2)
    return answer + int(palindrome <= n)


class Solution:
    def countBinaryPalindromes(self, n: int) -> int:
        return solve(n)
