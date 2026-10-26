"""3582. Generate Tag for Video Caption (Easy).

Specification: https://leetcode.com/problems/generate-tag-for-video-caption/description/
"""


def solve(caption: str) -> str:
    """O(n) time and space; caption contains only English letters and spaces."""
    words = caption.lower().split()
    parts = ['#']
    for index, word in enumerate(words):
        parts.append(word if index == 0 else word[0].upper() + word[1:])
    return ''.join(parts)[:100]


class Solution:
    def generateTag(self, caption: str) -> str:
        return solve(caption)
