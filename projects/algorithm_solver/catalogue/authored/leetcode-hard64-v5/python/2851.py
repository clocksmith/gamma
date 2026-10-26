"""2851. String Transformation. KMP counts matching rotations and a two-state matrix counts suffix moves."""


def solve(s: str, t: str, k: int) -> int:
    """O(n+log k) time and O(n) space. Inputs are preserved."""
    modulus = 1_000_000_007
    size = len(s)
    prefix = [0] * size
    for index in range(1, size):
        length = prefix[index - 1]
        while length and t[index] != t[length]:
            length = prefix[length - 1]
        if t[index] == t[length]:
            length += 1
        prefix[index] = length
    matches = 0
    length = 0
    for index in range(2 * size - 1):
        char = s[index % size]
        while length and char != t[length]:
            length = prefix[length - 1]
        if char == t[length]:
            length += 1
        if length == size:
            matches += 1
            length = prefix[length - 1]
    if matches == 0:
        return 0
    if matches == size:
        return pow(size - 1, k, modulus)

    def multiply(first, second):
        return [
            (first[0] * second[0] + first[1] * second[2]) % modulus,
            (first[0] * second[1] + first[1] * second[3]) % modulus,
            (first[2] * second[0] + first[3] * second[2]) % modulus,
            (first[2] * second[1] + first[3] * second[3]) % modulus,
        ]

    result = [1, 0, 0, 1]
    transition = [matches - 1, matches, size - matches, size - matches - 1]
    exponent = k
    while exponent:
        if exponent & 1:
            result = multiply(result, transition)
        transition = multiply(transition, transition)
        exponent //= 2
    return result[0] if s == t else result[1]


class Solution:
    def numberOfWays(self, s: str, t: str, k: int) -> int:
        return solve(s, t, k)
