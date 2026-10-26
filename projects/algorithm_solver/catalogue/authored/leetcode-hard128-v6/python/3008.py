"""3008. Find Beautiful Indices in the Given Array II.

Exact KMP occurrence lists joined by a monotone distance window; O(len(s)+len(a)+len(b)) time and space.
"""

def solve(s: str, a: str, b: str, k: int) -> list[int]:
    def occurrences(pattern):
        border = [0] * len(pattern)
        for index in range(1, len(pattern)):
            length = border[index - 1]
            while length and pattern[index] != pattern[length]:
                length = border[length - 1]
            border[index] = length + (pattern[index] == pattern[length])
        result = []
        length = 0
        for index, char in enumerate(s):
            while length and char != pattern[length]:
                length = border[length - 1]
            if char == pattern[length]:
                length += 1
            if length == len(pattern):
                result.append(index - length + 1)
                length = border[length - 1]
        return result

    first, second = occurrences(a), occurrences(b)
    answer = []
    index = 0
    for position in first:
        while index < len(second) and second[index] < position - k:
            index += 1
        if index < len(second) and second[index] <= position + k:
            answer.append(position)
    return answer


class Solution:
    def beautifulIndices(self, s: str, a: str, b: str, k: int) -> list[int]:
        return solve(s, a, b, k)
