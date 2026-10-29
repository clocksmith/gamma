"""Original frontend 758 variant; qualification unknown."""


def solve(words, s: str) -> str:
    n = len(s)
    bold = [False] * n
    for w in words:
        L = len(w)
        start = s.find(w)
        while start != -1:
            for i in range(start, start + L):
                bold[i] = True
            start = s.find(w, start + 1)
    out = []
    for i, ch in enumerate(s):
        if bold[i] and (i == 0 or not bold[i - 1]):
            out.append("<b>")
        out.append(ch)
        if bold[i] and (i == n - 1 or not bold[i + 1]):
            out.append("</b>")
    return "".join(out)


boldWords = solve


class Solution:
    def boldWords(self, words, s: str) -> str:
        return solve(words, s)
