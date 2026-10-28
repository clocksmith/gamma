"""Original frontend 3756 development candidate; qualification unknown."""

def solve(s, queries):
    modulus = 10**9 + 7
    values, counts, sums, powers = [0], [0], [0], [1]
    for char in s:
        digit = int(char)
        values.append((values[-1] * 10 + digit) % modulus if digit else values[-1])
        counts.append(counts[-1] + int(digit != 0))
        sums.append(sums[-1] + digit)
        powers.append(powers[-1] * 10 % modulus)
    return [((values[right + 1] - values[left] * powers[counts[right + 1] - counts[left]]) % modulus) * (sums[right + 1] - sums[left]) % modulus for left, right in queries]


class Solution:
    def sumAndMultiply(self, s, queries):
        return solve(s, queries)
