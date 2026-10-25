from math import gcd, isqrt


PRIME_BASES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)


def is_prime(value: int) -> bool:
    if value < 2:
        return False
    for prime in PRIME_BASES:
        if value % prime == 0:
            return value == prime
    odd = value - 1
    shifts = 0
    while odd % 2 == 0:
        odd //= 2
        shifts += 1
    for base in PRIME_BASES:
        residue = pow(base, odd, value)
        if residue == 1 or residue == value - 1:
            continue
        for _ in range(shifts - 1):
            residue = residue * residue % value
            if residue == value - 1:
                break
        else:
            return False
    return True


def split_factor(value: int, budget: list[int]) -> int:
    for constant in range(1, 17):
        position = constant + 1
        length = 1
        divisor = 1
        remaining = 65536
        checkpoint = position
        saved = position
        while divisor == 1 and remaining:
            checkpoint = position
            for _ in range(min(length, remaining)):
                if budget[0] <= 0:
                    raise RuntimeError("factorization work limit exhausted")
                budget[0] -= 1
                remaining -= 1
                position = (position * position + constant) % value
            offset = 0
            while offset < length and divisor == 1 and remaining:
                saved = position
                product = 1
                steps = min(64, length - offset, remaining)
                for _ in range(steps):
                    if budget[0] <= 0:
                        raise RuntimeError("factorization work limit exhausted")
                    budget[0] -= 1
                    remaining -= 1
                    position = (position * position + constant) % value
                    product = product * abs(checkpoint - position) % value
                divisor = gcd(product, value)
                offset += steps
            length *= 2
        if divisor == value:
            divisor = 1
            while divisor == 1 and remaining:
                if budget[0] <= 0:
                    raise RuntimeError("factorization work limit exhausted")
                budget[0] -= 1
                remaining -= 1
                saved = (saved * saved + constant) % value
                divisor = gcd(abs(checkpoint - saved), value)
        if 1 < divisor < value:
            return divisor
    raise RuntimeError("factorization seed limit exhausted")


class Solution:
    def judgeSquareSum(self, c: int) -> bool:
        if c < 2:
            return True
        root = isqrt(c)
        if root * root == c:
            return True
        for prime in PRIME_BASES:
            parity = 0
            while c % prime == 0:
                c //= prime
                parity ^= 1
            if prime % 4 == 3 and parity:
                return False
        pending = [c]
        odd_factors = set()
        budget = [1048576]
        while pending:
            value = pending.pop()
            if value == 1:
                continue
            if is_prime(value):
                if value % 4 == 3:
                    if value in odd_factors:
                        odd_factors.remove(value)
                    else:
                        odd_factors.add(value)
                continue
            root = isqrt(value)
            if root * root == value:
                continue
            factor = split_factor(value, budget)
            pending.extend((factor, value // factor))
        return not odd_factors
