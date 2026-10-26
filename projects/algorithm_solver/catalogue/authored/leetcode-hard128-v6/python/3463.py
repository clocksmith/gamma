"""3463. Check If Digits Are Equal in String After Operations II.

Compute binomial coefficients modulo two and five with Lucas digits, then combine modulo ten; O(n log n) time and O(1) space. Input is preserved.
"""

def solve(s: str) -> bool:
    small = ((1,), (1, 1), (1, 2, 1), (1, 3, 3, 1), (1, 4, 1, 4, 1))
    top = len(s) - 2
    difference = 0
    for index in range(top + 1):
        modulo_two = int(index & (top - index) == 0)
        first, second, modulo_five = top, index, 1
        while first or second:
            upper, lower = first % 5, second % 5
            if lower > upper:
                modulo_five = 0
                break
            modulo_five = modulo_five * small[upper][lower] % 5
            first //= 5
            second //= 5
        coefficient = modulo_five if modulo_five % 2 == modulo_two else modulo_five + 5
        difference = (difference + coefficient * (ord(s[index]) - ord(s[index + 1]))) % 10
    return difference == 0


class Solution:
    def hasSameDigits(self, s: str) -> bool:
        return solve(s)
