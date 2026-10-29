"""Hack2Hire 694af9676e481a4b09cbc77d (Design a Moderator System, level 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""
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


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ModSystem' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = ModSystem(*argument_lists[0])
    allowed = ['canRemove']
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
