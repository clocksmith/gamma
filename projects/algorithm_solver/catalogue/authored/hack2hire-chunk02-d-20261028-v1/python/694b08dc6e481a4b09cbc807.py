"""Hack2Hire 694b08dc6e481a4b09cbc807 (Design a Moderator System, level 3) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""
from bisect import bisect_right


class ModSystem:
    def __init__(self, logs):
        self.rank = {}
        self.history = {}
        for seq, (time, user, action) in enumerate(logs):
            active = user in self.rank
            if action == 'ADD' and not active:
                self.rank[user] = seq
            elif action == 'REMOVE' and active:
                del self.rank[user]
            else:
                continue
            times, ranks = self.history.setdefault(user, ([], []))
            times.append(time)
            ranks.append(self.rank.get(user, -1))
        self.order = sorted(self.rank, key=self.rank.get)

    def canRemove(self, actorId, targetId):
        rank = self.rank
        return actorId in rank and targetId in rank and rank[actorId] < rank[targetId]

    def getModerators(self):
        return list(self.order)

    def _rank_at(self, user, time):
        entry = self.history.get(user)
        if entry is None:
            return -1
        index = bisect_right(entry[0], time)
        return entry[1][index - 1] if index else -1

    def canRemoveAt(self, time, actorId, targetId):
        a, b = self._rank_at(actorId, time), self._rank_at(targetId, time)
        return a >= 0 and b >= 0 and a < b

    def getModeratorsAt(self, time):
        ranked = []
        for user in self.history:
            r = self._rank_at(user, time)
            if r >= 0:
                ranked.append((r, user))
        ranked.sort()
        return [user for _, user in ranked]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ModSystem' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = ModSystem(*argument_lists[0])
    allowed = ['canRemove', 'getModerators', 'canRemoveAt', 'getModeratorsAt']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
