"""1734. Decode XORed Permutation: recover the first value from odd-indexed pairs then decode adjacent XORs."""


def solve(encoded: list[int]) -> list[int]:
    """O(n) time and O(n) output space with O(1) auxiliary space; inputs are read-only."""
    first = 0
    for value in range(1, len(encoded) + 2):
        first ^= value
    for index in range(1, len(encoded), 2):
        first ^= encoded[index]
    answer = [first]
    for value in encoded:
        answer.append(answer[-1] ^ value)
    return answer


class Solution:
    def decode(self, encoded: list[int]) -> list[int]:
        return solve(encoded)
