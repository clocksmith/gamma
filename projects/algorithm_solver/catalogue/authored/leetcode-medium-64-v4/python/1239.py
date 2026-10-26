"""1239. Maximum Length of a Concatenated String with Unique Characters: combine disjoint lowercase-letter masks and discard words with repeated letters."""


def solve(arr: list[str]) -> int:
    """O(S + 2^n) time and O(2^n) auxiliary space for the fixed 26-letter alphabet; inputs are read-only."""
    states = [(0, 0)]
    best = 0
    for word in arr:
        mask = 0
        for letter in word:
            bit = 1 << (ord(letter) - ord('a'))
            if mask & bit:
                break
            mask |= bit
        else:
            for index in range(len(states)):
                used, length = states[index]
                if not used & mask:
                    combined = length + len(word)
                    states.append((used | mask, combined))
                    best = max(best, combined)
    return best


class Solution:
    def maxLength(self, arr: list[str]) -> int:
        return solve(arr)
