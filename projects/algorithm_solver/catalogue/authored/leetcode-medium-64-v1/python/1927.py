"""1927. Sum Game: compare the fixed digit imbalance with the unmatched question-mark contribution."""


def solve(num: str) -> bool:
    """O(n) time and O(1) auxiliary space; inputs are read-only."""
    middle = len(num) // 2
    difference = left_unknown = right_unknown = 0
    for index, character in enumerate(num):
        if character == '?':
            if index < middle:
                left_unknown += 1
            else:
                right_unknown += 1
        else:
            value = ord(character) - ord('0')
            difference += value if index < middle else -value
    if (left_unknown + right_unknown) % 2:
        return True
    return 2 * difference != 9 * (right_unknown - left_unknown)


class Solution:
    def sumGame(self, num: str) -> bool:
        return solve(num)
