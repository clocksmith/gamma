"""2129. Capitalize the Title (Easy).

Specification: https://leetcode.com/problems/capitalize-the-title/description/
"""


def solve(title: str) -> str:
    words = []
    for word in title.split(' '):
        lower = word.lower()
        if len(lower) <= 2:
            words.append(lower)
        else:
            words.append(lower[0].upper() + lower[1:])
    return ' '.join(words)


class Solution:
    def capitalizeTitle(self, title: str) -> str:
        return solve(title)
