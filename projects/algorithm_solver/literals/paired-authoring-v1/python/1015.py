def prime_factors(value: int) -> list[int]:
    factors = []
    divisor = 2
    while divisor * divisor <= value:
        if value % divisor == 0:
            factors.append(divisor)
            while value % divisor == 0:
                value //= divisor
        divisor = 3 if divisor == 2 else divisor + 2
    if value > 1:
        factors.append(value)
    return factors


def modular_power(base: int, exponent: int, modulus: int) -> int:
    result = 1
    base %= modulus
    while exponent > 0:
        if exponent % 2 == 1:
            result = result * base % modulus
        base = base * base % modulus
        exponent //= 2
    return result


class Solution:
    def smallestRepunitDivByK(self, k: int) -> int:
        if k % 2 == 0 or k % 5 == 0:
            return -1
        modulus = 9 * k
        order = modulus
        for factor in prime_factors(modulus):
            order = order // factor * (factor - 1)
        for factor in prime_factors(order):
            while order % factor == 0:
                candidate = order // factor
                if modular_power(10, candidate, modulus) != 1:
                    break
                order = candidate
        return order
