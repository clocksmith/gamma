"""1410. HTML Entity Parser (Medium).

Specification: https://leetcode.com/problems/html-entity-parser/description/
"""


def solve(text):
    return (
        text.replace("&quot;", '"')
        .replace("&apos;", "'")
        .replace("&gt;", ">")
        .replace("&lt;", "<")
        .replace("&frasl;", "/")
        .replace("&amp;", "&")
    )


class Solution:
    def entityParser(self, text):
        return solve(text)
