"""2953. Count Complete Substrings."""

def solve(word: str, k: int) -> int:
    """O(26*n) time, O(n+26) space; split on bad adjacent gaps, then count fixed windows."""
    letters = [ord(char) - 97 for char in word]
    answer = 0
    start = 0
    while start < len(letters):
        stop = start + 1
        while stop < len(letters) and abs(letters[stop] - letters[stop - 1]) <= 2:
            stop += 1
        for distinct in range(1, min(26, (stop - start) // k) + 1):
            width = distinct * k
            counts = [0] * 26
            exact = 0
            for right in range(start, stop):
                letter = letters[right]
                if counts[letter] == k:
                    exact -= 1
                counts[letter] += 1
                if counts[letter] == k:
                    exact += 1
                if right - start >= width:
                    outgoing = letters[right - width]
                    if counts[outgoing] == k:
                        exact -= 1
                    counts[outgoing] -= 1
                    if counts[outgoing] == k:
                        exact += 1
                if right - start + 1 >= width and exact == distinct:
                    answer += 1
        start = stop
    return answer


class Solution:
    def countCompleteSubstrings(self, word: str, k: int) -> int:
        return solve(word, k)
