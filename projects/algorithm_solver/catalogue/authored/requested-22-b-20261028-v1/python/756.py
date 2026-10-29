"""Original frontend 756 variant; qualification unknown."""

def solve(bottom, allowed):
    top = [0] * 36
    for pattern in allowed:
        top[(ord(pattern[0]) - 65) * 6 + ord(pattern[1]) - 65] |= 1 << (ord(pattern[2]) - 65)
    memo = {}

    def can(row):
        if len(row) == 1:
            return True
        if row in memo:
            return memo[row]
        following = []

        def build(i):
            if i == len(row) - 1:
                return can(tuple(following))
            mask = top[row[i] * 6 + row[i + 1]]
            for c in range(6):
                if not mask >> c & 1:
                    continue
                if i and not top[following[-1] * 6 + c]:
                    continue
                following.append(c)
                if build(i + 1):
                    following.pop()
                    return True
                following.pop()
            return False

        memo[row] = build(0)
        return memo[row]

    return can(tuple(ord(ch) - 65 for ch in bottom))


class Solution:
    def pyramidTransition(self, bottom, allowed):
        return solve(bottom, allowed)
