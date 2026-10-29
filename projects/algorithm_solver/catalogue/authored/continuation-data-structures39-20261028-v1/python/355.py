"""Original frontend 355 variant; qualification unknown."""
import heapq


class Twitter:
    def __init__(self):
        self.time = 0
        self.tweets = {}
        self.following = {}

    def postTweet(self, userId: int, tweetId: int) -> None:
        self.time += 1
        bucket = self.tweets.setdefault(userId, [])
        bucket.append((self.time, tweetId))
        if len(bucket) > 10:
            del bucket[0]

    def getNewsFeed(self, userId: int):
        users = set(self.following.get(userId, ()))
        users.add(userId)
        heap = []
        for u in users:
            tlist = self.tweets.get(u)
            if tlist:
                idx = len(tlist) - 1
                ts, tid = tlist[idx]
                heapq.heappush(heap, (-ts, tid, tlist, idx - 1))
        res = []
        while heap and len(res) < 10:
            neg_ts, tid, tlist, prev_idx = heapq.heappop(heap)
            res.append(tid)
            if prev_idx >= 0:
                ts2, tid2 = tlist[prev_idx]
                heapq.heappush(heap, (-ts2, tid2, tlist, prev_idx - 1))
        return res

    def follow(self, followerId: int, followeeId: int) -> None:
        if followerId != followeeId:
            self.following.setdefault(followerId, set()).add(followeeId)

    def unfollow(self, followerId: int, followeeId: int) -> None:
        s = self.following.get(followerId)
        if s is not None:
            s.discard(followeeId)


def solve(operation_names, argument_lists):
    instance = Twitter()
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "postTweet":
            instance.postTweet(args[0], args[1])
            out.append(None)
        elif op == "getNewsFeed":
            out.append(instance.getNewsFeed(args[0]))
        elif op == "follow":
            instance.follow(args[0], args[1])
            out.append(None)
        elif op == "unfollow":
            instance.unfollow(args[0], args[1])
            out.append(None)
        else:
            raise ValueError("unknown operation")
    return out
