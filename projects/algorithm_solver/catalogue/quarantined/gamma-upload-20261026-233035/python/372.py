"""372. Super Pow."""
MODULUS = 1337

def solve(a: int, b: list[int]) -> int:
    result = 1
    base = a % MODULUS
    for digit in b:
        result = pow(result, 10, MODULUS) * pow(base, digit, MODULUS) % MODULUS
    return result

class Solution:
    def superPow(self, a: int, b: list[int]) -> int:
        return solve(a, b)
