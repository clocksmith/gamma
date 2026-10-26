"""2515. Shortest Distance to Target String in a Circular Array (Easy).

Specification: https://leetcode.com/problems/shortest-distance-to-target-string-in-a-circular-array/description/
"""


def solve(words: list[str], target: str, startIndex: int) -> int:
    """O(total compared characters) time, O(1) space; minimize clockwise/counterclockwise distance; preserve words."""
    best = len(words)
    for index, word in enumerate(words):
        if word != target:
            continue
        distance = abs(index - startIndex)
        best = min(best, distance, len(words) - distance)
    return -1 if best == len(words) else best


class Solution:
    def closetTarget(self, words: list[str], target: str, startIndex: int) -> int:
        return solve(words, target, startIndex)
