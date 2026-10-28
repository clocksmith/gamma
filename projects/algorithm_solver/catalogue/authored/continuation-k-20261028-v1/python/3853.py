def solve(s, k):
    while True:
        merged = False
        for l in range(len(s)):
            for r in range(l + 1, min(len(s), l + k + 1)):
                if s[l] == s[r]:
                    s = s[:r] + s[r + 1:]
                    merged = True
                    break
            if merged:
                break
        if not merged:
            return s


class Solution:
    def mergeCharacters(self, s, k):
        return solve(s, k)
