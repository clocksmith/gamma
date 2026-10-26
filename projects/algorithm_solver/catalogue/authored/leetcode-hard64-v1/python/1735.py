"""1735. Count Ways to Make Array With Product: prime exponents and stars-and-bars combinations."""


def solve(queries: list[list[int]]) -> list[int]:
    """O(M + Q*sqrt(K) + Q*log(K)) time and O(M) space, M=max(n)+floor(log2(K)). Inputs are preserved."""
    modulus = 1_000_000_007
    maximum_n = max(query[0] for query in queries)
    maximum_k = max(query[1] for query in queries)
    limit = maximum_n + maximum_k.bit_length()
    factorial = [1] * (limit + 1)
    for index in range(1, limit + 1):
        factorial[index] = factorial[index - 1] * index % modulus
    inverse = [1] * (limit + 1)
    inverse[limit] = pow(factorial[limit], modulus - 2, modulus)
    for index in range(limit, 0, -1):
        inverse[index - 1] = inverse[index] * index % modulus

    def choose(total, count):
        return factorial[total] * inverse[count] % modulus * inverse[total - count] % modulus

    answers = []
    for length, product in queries:
        remaining = product
        prime = 2
        ways = 1
        while prime * prime <= remaining:
            exponent = 0
            while remaining % prime == 0:
                remaining //= prime
                exponent += 1
            if exponent:
                ways = ways * choose(length + exponent - 1, exponent) % modulus
            prime += 1
        if remaining > 1:
            ways = ways * length % modulus
        answers.append(ways)
    return answers


class Solution:
    def waysToFillArray(self, queries: list[list[int]]) -> list[int]:
        return solve(queries)
