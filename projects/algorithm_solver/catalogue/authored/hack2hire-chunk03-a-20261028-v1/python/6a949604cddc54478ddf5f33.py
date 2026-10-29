"""Hack2Hire 6a949604cddc54478ddf5f33 (Maximize Deployment Score) over an INFERRED spec; qualification unknown."""


def solve(difficulty):
    s = sorted(difficulty)
    return (s[-1] - s[0]) + max(s[-2] - s[0], s[-1] - s[1])


class Solution:
    def maxDeploymentScore(self, difficulty):
        return solve(difficulty)
