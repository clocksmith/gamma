"""Original frontend 1229 variant; qualification unknown."""


def solve(slots1, slots2, duration: int):
    a = sorted(s for s in slots1 if s[1] - s[0] >= duration)
    b = sorted(s for s in slots2 if s[1] - s[0] >= duration)
    i = j = 0
    while i < len(a) and j < len(b):
        lo = max(a[i][0], b[j][0])
        hi = min(a[i][1], b[j][1])
        if hi - lo >= duration:
            return [lo, lo + duration]
        if a[i][1] < b[j][1]:
            i += 1
        else:
            j += 1
    return []


minAvailableDuration = solve


class Solution:
    def minAvailableDuration(self, slots1, slots2, duration: int):
        return solve(slots1, slots2, duration)
