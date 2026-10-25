class Solution:
    def queryString(self, s, n):
        seen = set()
        for start in range(len(s)):
            if s[start] == "0":
                continue
            value = 0
            for end in range(start, len(s)):
                value = value * 2 + (1 if s[end] == "1" else 0)
                if value > n:
                    break
                seen.add(value)
                if len(seen) == n:
                    return True
        return len(seen) == n
