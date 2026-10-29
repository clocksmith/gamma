"""Hack2Hire 69557dad4a0202df9569e983 (Related Communities Finder, variant 2 of 2) over an INFERRED spec; qualification unknown."""


def solve(communityToFollowers, followerToCommunities, communityIdx):
    n = len(communityToFollowers)
    if not 0 <= communityIdx < n:
        return []
    seen_community = [False] * n
    seen_follower = [False] * len(followerToCommunities)
    seen_community[communityIdx] = True
    queue = [communityIdx]
    head = 0
    while head < len(queue):
        community = queue[head]
        head += 1
        for follower in communityToFollowers[community]:
            j = int(follower[1:])
            if seen_follower[j]:
                continue
            seen_follower[j] = True
            for other in followerToCommunities[j]:
                k = int(other[1:])
                if not seen_community[k]:
                    seen_community[k] = True
                    queue.append(k)
    seen_community[communityIdx] = False
    return ['C%d' % i for i in range(n) if seen_community[i]]


class Solution:
    def findConnectedCommunities(self, communityToFollowers, followerToCommunities, communityIdx):
        return solve(communityToFollowers, followerToCommunities, communityIdx)
