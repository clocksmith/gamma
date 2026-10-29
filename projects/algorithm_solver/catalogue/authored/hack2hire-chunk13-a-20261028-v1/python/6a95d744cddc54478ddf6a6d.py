"""Hack2Hire 6a95d744cddc54478ddf6a6d (Optimal Team Selection) over an INFERRED spec; qualification unknown."""


def _feasible(lowerSkill, higherSkill, k):
    taken = 0
    for i in range(len(lowerSkill)):
        if taken <= lowerSkill[i] and k - 1 - taken <= higherSkill[i]:
            taken += 1
            if taken == k:
                return True
    return False


def solve(lowerSkill, higherSkill):
    lo, hi = 1, len(lowerSkill)  # a single developer is always a valid team
    while lo < hi:
        mid = (lo + hi + 1) // 2
        if _feasible(lowerSkill, higherSkill, mid):
            lo = mid
        else:
            hi = mid - 1
    return lo


class Solution:
    def maxTeamSize(self, lowerSkill, higherSkill):
        return solve(lowerSkill, higherSkill)
