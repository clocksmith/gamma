"""355. Design Twitter."""
import heapq
from collections import defaultdict

class Twitter:
    def __init__(self):
        self.time = 0
        self.posts = defaultdict(list)
        self.following = defaultdict(set)

    def postTweet(self, userId: int, tweetId: int) -> None:
        self.time += 1
        self.posts[userId].append((self.time, tweetId))

    def getNewsFeed(self, userId: int) -> list[int]:
        users = self.following[userId] | {userId}
        heap = []
        for user in users:
            for timestamp, tweet in self.posts[user][-10:]:
                heapq.heappush(heap, (timestamp, tweet))
                if len(heap) > 10:
                    heapq.heappop(heap)
        return [tweet for _, tweet in sorted(heap, reverse=True)]

    def follow(self, followerId: int, followeeId: int) -> None:
        self.following[followerId].add(followeeId)

    def unfollow(self, followerId: int, followeeId: int) -> None:
        self.following[followerId].discard(followeeId)

def solve(operations: list[str], arguments: list[list[int]]) -> list:
    twitter = Twitter()
    result = []
    for operation, values in zip(operations, arguments):
        if operation == 'Twitter':
            result.append(None)
        else:
            result.append(getattr(twitter, operation)(*values))
    return result
