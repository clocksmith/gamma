"""3145. Find Products of Elements of Big Array.

Binary search complete integer blocks using set-bit counts, then sum their exponents; O(q*log^2 M) time. JavaScript uses BigInt for large index arithmetic.
"""

def solve(queries: list[list[int]]) -> list[int]:
    def statistics(limit):
        count = exponent = 0
        power = 1
        bit = 0
        while power <= limit:
            cycle = 2 * power
            ones = (limit + 1) // cycle * power + max(0, (limit + 1) % cycle - power)
            count += ones
            exponent += bit * ones
            power *= 2
            bit += 1
        return count, exponent

    def prefix(length):
        low, high = 0, length
        while low < high:
            middle = (low + high + 1) // 2
            if statistics(middle)[0] <= length:
                low = middle
            else:
                high = middle - 1
        complete, exponent = statistics(low)
        remaining = length - complete
        value = low + 1
        bit = 0
        while remaining:
            if value >> bit & 1:
                exponent += bit
                remaining -= 1
            bit += 1
        return exponent

    return [pow(2, prefix(right + 1) - prefix(left), modulus) for left, right, modulus in queries]


class Solution:
    def findProductsOfElements(self, queries: list[list[int]]) -> list[int]:
        return solve(queries)
