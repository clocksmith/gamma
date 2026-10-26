"""1737. Change Minimum Characters to Satisfy One of Three Conditions: compare shared-letter costs with every strict alphabet boundary."""


def solve(a: str, b: str) -> int:
    """O(len(a) + len(b) + 26) time and O(26) auxiliary space; inputs are read-only."""
    first = [0] * 26
    second = [0] * 26
    for letter in a:
        first[ord(letter) - ord('a')] += 1
    for letter in b:
        second[ord(letter) - ord('a')] += 1
    result = len(a) + len(b) - max(first[i] + second[i] for i in range(26))
    first_prefix = second_prefix = 0
    for boundary in range(25):
        first_prefix += first[boundary]
        second_prefix += second[boundary]
        result = min(result, len(a) - first_prefix + second_prefix,
                     len(b) - second_prefix + first_prefix)
    return result


class Solution:
    def minCharacters(self, a: str, b: str) -> int:
        return solve(a, b)
