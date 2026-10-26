"""2531. Make Number of Distinct Characters Equal: evaluate each available letter swap by its effect on distinct counts."""


def solve(word1: str, word2: str) -> bool:
    """O(n + m + 26^2) time and O(1) auxiliary space; inputs are read-only."""
    first = [0] * 26
    second = [0] * 26
    for character in word1:
        first[ord(character) - ord('a')] += 1
    for character in word2:
        second[ord(character) - ord('a')] += 1
    first_distinct = sum(count > 0 for count in first)
    second_distinct = sum(count > 0 for count in second)
    for left in range(26):
        if first[left] == 0:
            continue
        for right in range(26):
            if second[right] == 0:
                continue
            if left == right:
                if first_distinct == second_distinct:
                    return True
                continue
            next_first = first_distinct - (first[left] == 1) + (first[right] == 0)
            next_second = second_distinct - (second[right] == 1) + (second[left] == 0)
            if next_first == next_second:
                return True
    return False


class Solution:
    def isItPossible(self, word1: str, word2: str) -> bool:
        return solve(word1, word2)
