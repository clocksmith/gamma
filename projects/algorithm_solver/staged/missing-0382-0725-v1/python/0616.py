"""616. Add Bold Tag in String. Merge overlapping and adjacent matching intervals before emitting tags."""

def solve(s: str, words: list[str]) -> str:
    difference = [0] * (len(s) + 1)
    for word in words:
        if not word:
            continue
        start = s.find(word)
        while start != -1:
            difference[start] += 1
            difference[start + len(word)] -= 1
            start = s.find(word, start + 1)
    parts = []
    active = 0
    for i, char in enumerate(s):
        before = active
        active += difference[i]
        if before == 0 and active:
            parts.append('<b>')
        elif before and active == 0:
            parts.append('</b>')
        parts.append(char)
    if active:
        parts.append('</b>')
    return ''.join(parts)


class Solution:
    def addBoldTag(self, s: str, words: list[str]) -> str:
        return solve(s, words)
