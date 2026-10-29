"""Hack2Hire 68f5af31a269f53ea0eff8a0 (Highest Scoring Movie Group) over an INFERRED spec; qualification unknown."""

import heapq


def solve(similarityScores, groups, k):
    best_index = -1
    best_total = -1
    for index, group in enumerate(groups):
        heap = []
        for movie in group:
            heapq.heappush(heap, similarityScores[movie])
            if len(heap) > k:
                heapq.heappop(heap)
        total = sum(heap)
        if total > best_total:
            best_total = total
            best_index = index
    return best_index


class Solution:
    def findHighestScoringGroup(self, similarityScores, groups, k):
        return solve(similarityScores, groups, k)
