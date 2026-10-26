"""1711. Count Good Meals: count earlier complements for each possible power-of-two sum."""


def solve(deliciousness: list[int]) -> int:
    """O(22 * n) time and O(n) auxiliary space on the stated value domain; inputs are read-only."""
    frequencies = {}
    answer = 0
    modulus = 1_000_000_007
    for value in deliciousness:
        power = 1
        for _ in range(22):
            answer = (answer + frequencies.get(power - value, 0)) % modulus
            power *= 2
        frequencies[value] = frequencies.get(value, 0) + 1
    return answer


class Solution:
    def countPairs(self, deliciousness: list[int]) -> int:
        return solve(deliciousness)
