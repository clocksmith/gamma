from functools import cache
class Solution:

    def isMatch(self, s, p):

        @cache
        def dfs(i, j):
            if i >= len(s):
                return j >= len(p) or (p[j] == '*' and dfs(i, j + 1))
            if j >= len(p):
                return False
            if p[j] == '*':
                return dfs(i + 1, j) or dfs(i + 1, j + 1) or dfs(i, j + 1)
            return (p[j] == '?' or s[i] == p[j]) and dfs(i + 1, j + 1)
        return dfs(0, 0)
