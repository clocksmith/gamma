"""Hack2Hire 68e2d042dab409e303d92952 (Friends by Last-K Movie Overlap, variant 2 of 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from bisect import bisect_left, insort
from collections import deque


class MovieFriends:
    def __init__(self, k):
        self.k = k
        self.window = {}    # customer -> deque of the last k movies
        self.counts = {}    # customer -> {movie: count inside the window}
        self.distinct = {}  # customer -> sorted distinct movies of the window
        self.key = {}       # customer -> current key (only once the window is full)
        self.buckets = {}   # key -> sorted customers

    def watch(self, customerId, movieId):
        window = self.window.get(customerId)
        if window is None:
            window = self.window[customerId] = deque()
            self.counts[customerId] = {}
            self.distinct[customerId] = []
        counts, distinct = self.counts[customerId], self.distinct[customerId]
        window.append(movieId)
        counts[movieId] = counts.get(movieId, 0) + 1
        if counts[movieId] == 1:
            insort(distinct, movieId)
        if len(window) > self.k:
            old = window.popleft()
            counts[old] -= 1
            if counts[old] == 0:
                del counts[old]
                del distinct[bisect_left(distinct, old)]
        if len(window) == self.k:
            new = ','.join(distinct)
            old_key = self.key.get(customerId)
            if new != old_key:
                if old_key is not None:
                    bucket = self.buckets[old_key]
                    del bucket[bisect_left(bucket, customerId)]
                    if not bucket:
                        del self.buckets[old_key]
                insort(self.buckets.setdefault(new, []), customerId)
                self.key[customerId] = new

    def getFriends(self, customerId):
        key = self.key.get(customerId)
        if key is None:
            return []
        return [c for c in self.buckets[key] if c != customerId]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'MovieFriends' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = MovieFriends(*argument_lists[0])
    allowed = {'watch', 'getFriends'}
    voids = {'watch'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
