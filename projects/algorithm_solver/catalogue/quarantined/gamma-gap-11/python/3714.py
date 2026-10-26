"""3714. Longest Balanced Substring II."""
from __future__ import annotations


def solve(s: str) -> int:
    """O(n) expected time and O(n) space; separately consider one, two, and three distinct letters."""
    answer = run = 0
    previous = ''
    for char in s:
        run = run + 1 if char == previous else 1
        previous = char
        answer = max(answer, run)
    for first, second in (('a', 'b'), ('a', 'c'), ('b', 'c')):
        earliest = {0: -1}
        difference = 0
        for index, char in enumerate(s):
            if char != first and char != second:
                earliest = {0: index}
                difference = 0
                continue
            difference += 1 if char == first else -1
            if difference in earliest:
                answer = max(answer, index - earliest[difference])
            else:
                earliest[difference] = index
    counts = [0, 0, 0]
    earliest = {(0, 0): -1}
    for index, char in enumerate(s):
        counts[ord(char) - 97] += 1
        key = (counts[0] - counts[1], counts[0] - counts[2])
        if key in earliest:
            answer = max(answer, index - earliest[key])
        else:
            earliest[key] = index
    return answer


class Solution:
    def longestBalanced(self, s: str) -> int:
        return solve(s)
