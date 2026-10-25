"""1542. Find Longest Awesome Substring."""

def solve(s: str) -> int:
    """O(10*n) time, O(2^10) space; valid intervals have at most one odd count."""
    first = [len(s)] * 1024
    first[0] = -1
    mask = 0
    answer = 0
    for index, char in enumerate(s):
        mask ^= 1 << (ord(char) - 48)
        answer = max(answer, index - first[mask])
        for digit in range(10):
            answer = max(answer, index - first[mask ^ (1 << digit)])
        if first[mask] == len(s):
            first[mask] = index
    return answer


class Solution:
    def longestAwesome(self, s: str) -> int:
        return solve(s)
