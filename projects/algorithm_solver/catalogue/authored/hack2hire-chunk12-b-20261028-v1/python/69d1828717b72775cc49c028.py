"""Hack2Hire 69d1828717b72775cc49c028 (Nested String with Brackets Parsing, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def solve(s):
    stack = []
    result = None
    word_start = -1
    for i, ch in enumerate(s):
        if 'a' <= ch <= 'z':
            if word_start < 0:
                word_start = i
            continue
        if word_start >= 0:
            stack[-1].append(s[word_start:i])
            word_start = -1
        if ch == '(':
            stack.append([])
        elif ch == ')':
            done = stack.pop()
            if stack:
                stack[-1].append(done)
            else:
                result = done
    return result


class Solution:
    def parseNested(self, s):
        return solve(s)
