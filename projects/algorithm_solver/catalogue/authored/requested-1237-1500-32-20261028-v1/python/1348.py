"""Original frontend 1348 variant; qualification unknown."""


class TweetCounts:
    def __init__(self):
        self.tweets = {}

    def recordTweet(self, tweetName: str, time: int) -> None:
        self.tweets.setdefault(tweetName, []).append(time)

    def getTweetCountsPerFrequency(self, freq: str, tweetName: str, startTime: int, endTime: int):
        delta = 60 if freq == "minute" else (3600 if freq == "hour" else 86400)
        buckets = [0] * (((endTime - startTime) // delta) + 1)
        for t in self.tweets.get(tweetName, ()):
            if startTime <= t <= endTime:
                buckets[(t - startTime) // delta] += 1
        return buckets


def solve(operation_names, argument_lists):
    inst = TweetCounts()
    out = [None]
    for op, args in zip(operation_names[1:], argument_lists[1:]):
        if op == "recordTweet":
            inst.recordTweet(args[0], args[1])
            out.append(None)
        else:
            out.append(inst.getTweetCountsPerFrequency(args[0], args[1], args[2], args[3]))
    return out
