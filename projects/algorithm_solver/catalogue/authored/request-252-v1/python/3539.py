from math import comb


def solve(m, k, nums):
    modulus = 1_000_000_007
    choose = [[comb(remaining, count) for count in range(remaining + 1)]
              for remaining in range(m + 1)]
    # A state records positions assigned, carry into this bit, and finalized ones.
    states = {(0, 0, 0): 1}
    for value in nums:
        powers = [1]
        for count in range(m):
            powers.append(powers[-1] * value % modulus)
        weights = [[coefficient * powers[count] % modulus
                    for count, coefficient in enumerate(row)] for row in choose]
        following = {}
        for (used, carry, ones), ways in states.items():
            for count in range(m - used + 1):
                total = carry + count
                next_ones = ones + total % 2
                if next_ones > k:
                    continue
                key = (used + count, total // 2, next_ones)
                contribution = ways * weights[m - used][count]
                following[key] = (following.get(key, 0) + contribution) % modulus
        states = following
    return sum(ways for (used, carry, ones), ways in states.items()
               if used == m and ones + carry.bit_count() == k) % modulus
