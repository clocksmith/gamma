class Solution:
    def numsSameConsecDiff(self, n, k):
        prefixes = list(range(1, 10))
        for _ in range(1, n):
            following = []
            for prefix in prefixes:
                last = prefix % 10
                lower = last - k
                upper = last + k
                if lower >= 0:
                    following.append(prefix * 10 + lower)
                if k != 0 and upper <= 9:
                    following.append(prefix * 10 + upper)
            prefixes = following
        return prefixes
