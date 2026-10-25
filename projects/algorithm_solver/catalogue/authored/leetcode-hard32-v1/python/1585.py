"""1585. Check If String Is Transformable With Substring Sort Operations."""

def solve(s: str, t: str) -> bool:
    """O(10*n) time, O(n) space; smaller unused digits block a digit moving left."""
    positions = [[] for _ in range(10)]
    for index, char in enumerate(s):
        positions[ord(char) - 48].append(index)
    heads = [0] * 10
    for char in t:
        digit = ord(char) - 48
        if heads[digit] == len(positions[digit]):
            return False
        position = positions[digit][heads[digit]]
        for smaller in range(digit):
            if (heads[smaller] < len(positions[smaller])
                    and positions[smaller][heads[smaller]] < position):
                return False
        heads[digit] += 1
    return True


class Solution:
    def isTransformable(self, s: str, t: str) -> bool:
        return solve(s, t)
