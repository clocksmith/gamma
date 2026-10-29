"""Hack2Hire 69b1936ca4e93c007df40055 (Snapshot Social Graph, level 3) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from bisect import bisect_right


class SocialNetwork:
    def __init__(self):
        self.current = 0
        self.history = {}
        self.touched = {}

    def _record(self, follower, followee, state):
        key = (follower, followee)
        entry = self.history.get(key)
        if entry is None:
            if not state:
                return
            entry = self.history[key] = ([], [])
            self.touched.setdefault(follower, []).append(followee)
        snaps, states = entry
        if snaps and snaps[-1] == self.current:
            states[-1] = state
        else:
            snaps.append(self.current)
            states.append(state)

    def _at(self, follower, followee, snapshotId):
        entry = self.history.get((follower, followee))
        if entry is None:
            return False
        i = bisect_right(entry[0], snapshotId) - 1
        return i >= 0 and entry[1][i]

    def follow(self, followerId, followeeId):
        self._record(followerId, followeeId, True)

    def unfollow(self, followerId, followeeId):
        self._record(followerId, followeeId, False)

    def snapshot(self):
        self.current += 1
        return self.current - 1

    def isFollowing(self, followerId, followeeId, snapshotId):
        return self._at(followerId, followeeId, snapshotId)

    def getFollowees(self, userId, snapshotId):
        return sorted(e for e in self.touched.get(userId, ()) if self._at(userId, e, snapshotId))

    def recommend(self, userId, snapshotId, k):
        mine = self.getFollowees(userId, snapshotId)
        excluded = set(mine)
        excluded.add(userId)
        score = {}
        for v in mine:
            for w in self.touched.get(v, ()):
                if w not in excluded and self._at(v, w, snapshotId):
                    score[w] = score.get(w, 0) + 1
        return sorted(score, key=lambda w: (-score[w], w))[:k]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'SocialNetwork' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = SocialNetwork(*argument_lists[0])
    allowed = ['follow', 'unfollow', 'snapshot', 'isFollowing', 'getFollowees', 'recommend']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in ['follow', 'unfollow'] else value)
    return result
