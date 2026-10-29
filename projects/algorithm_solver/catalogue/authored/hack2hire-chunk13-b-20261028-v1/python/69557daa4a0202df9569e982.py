"""Hack2Hire 69557daa4a0202df9569e982 (Related Communities Finder, variant 1 of 2) over an INFERRED spec; qualification unknown."""


def solve(communityToFollowers, followerToCommunities, communityIdx):
    n = len(communityToFollowers)
    if not 0 <= communityIdx < n:
        return []
    marked = [False] * n
    for follower in communityToFollowers[communityIdx]:
        for community in followerToCommunities[int(follower[1:])]:
            marked[int(community[1:])] = True
    marked[communityIdx] = False
    return ['C%d' % i for i in range(n) if marked[i]]


class Solution:
    def findRelatedCommunities(self, communityToFollowers, followerToCommunities, communityIdx):
        return solve(communityToFollowers, followerToCommunities, communityIdx)
