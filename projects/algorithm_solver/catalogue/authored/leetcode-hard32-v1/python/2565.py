"""2565. Subsequence With the Minimum Score."""

def solve(s: str, t: str) -> int:
    """O(len(s)+len(t)) time, O(len(t)) space; join a matched prefix to a latest suffix."""
    source_size, target_size = len(s), len(t)
    right = [-1] * (target_size + 1)
    right[target_size] = source_size
    position = source_size - 1
    for index in range(target_size - 1, -1, -1):
        while position >= 0 and s[position] != t[index]:
            position -= 1
        right[index] = position
        if position >= 0:
            position -= 1
    suffix = 0
    while suffix < target_size and right[suffix] < 0:
        suffix += 1
    answer = suffix
    position = -1
    for prefix_size in range(1, target_size + 1):
        position += 1
        while position < source_size and s[position] != t[prefix_size - 1]:
            position += 1
        if position == source_size:
            break
        suffix = max(suffix, prefix_size)
        while right[suffix] <= position:
            suffix += 1
        answer = min(answer, suffix - prefix_size)
        if answer == 0:
            return 0
    return answer


class Solution:
    def minimumScore(self, s: str, t: str) -> int:
        return solve(s, t)
