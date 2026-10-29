"""Hack2Hire 699bb8776e73e4abccc9aa11 (Generate Unique Usernames) over an INFERRED spec; qualification unknown."""


def solve(names):
    issued = set()
    next_suffix = {}  # base -> first suffix not yet tried for it
    out = []
    for name in names:
        words = name.split(' ')
        base = (words[0][0] + words[-1]).lower()[:8]
        user = base
        if base in issued:
            k = next_suffix.get(base, 1)
            while True:
                digits = str(k)
                user = base[:8 - len(digits)] + digits
                if user not in issued:
                    break
                k += 1
            next_suffix[base] = k + 1
        issued.add(user)
        out.append(user)
    return out


class Solution:
    def generateUsernames(self, names):
        return solve(names)
