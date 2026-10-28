"""1311. Get Watched Videos by Your Friends (Medium).

Specification: https://leetcode.com/problems/get-watched-videos-by-your-friends/description/
"""


def solve(watchedVideos, friends, id, level):
    seen = {id}
    frontier = [id]
    for _ in range(level):
        nxt = []
        for person in frontier:
            for friend in friends[person]:
                if friend not in seen:
                    seen.add(friend)
                    nxt.append(friend)
        frontier = nxt
    counts = {}
    for person in frontier:
        for video in watchedVideos[person]:
            counts[video] = counts.get(video, 0) + 1
    return [name for name, _ in sorted(counts.items(), key=lambda item: (item[1], item[0]))]


class Solution:
    def watchedVideosByFriends(self, watchedVideos, friends, id, level):
        return solve(watchedVideos, friends, id, level)
