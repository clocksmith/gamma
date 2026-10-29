"""Original frontend 320 variant; qualification unknown."""


def solve(word: str):
    n = len(word)
    out = []
    for mask in range(1 << n):
        parts = []
        cnt = 0
        for i in range(n):
            if (mask >> i) & 1:
                cnt += 1
            else:
                if cnt > 0:
                    parts.append(str(cnt))
                    cnt = 0
                parts.append(word[i])
        if cnt > 0:
            parts.append(str(cnt))
        out.append("".join(parts))
    return out


generateAbbreviations = solve


class Solution:
    def generateAbbreviations(self, word: str):
        return solve(word)
