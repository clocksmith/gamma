"""Hack2Hire 681bc967a73bd75b806cb994 (Escape Room) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class EscapeRoom:
    def __init__(self, n, m):
        self.n = n
        self.room = [0] * m
        self.prev = [p - 1 for p in range(m)]
        self.next = [p + 1 if p + 1 < m else -1 for p in range(m)]
        self.head = [-1] * n
        self.tail = [-1] * n
        self.count = [0] * n
        self.head[0], self.tail[0], self.count[0] = 0, m - 1, m
        # non-empty rooms in decreasing order, as a linked list
        self.lower = [-1] * n
        self.higher = [-1] * n
        self.top = 0

    def advance(self, player):
        r = self.room[player]
        if r == self.n - 1:
            return
        p, q = self.prev[player], self.next[player]
        if p >= 0:
            self.next[p] = q
        else:
            self.head[r] = q
        if q >= 0:
            self.prev[q] = p
        else:
            self.tail[r] = p
        s = r + 1
        if self.count[s] == 0:
            above = self.higher[r]
            self.higher[s], self.lower[s] = above, r
            self.higher[r] = s
            if above >= 0:
                self.lower[above] = s
            else:
                self.top = s
        t = self.tail[s]
        self.prev[player], self.next[player] = t, -1
        if t >= 0:
            self.next[t] = player
        else:
            self.head[s] = player
        self.tail[s] = player
        self.count[s] += 1
        self.room[player] = s
        self.count[r] -= 1
        if self.count[r] == 0:
            below, above = self.lower[r], self.higher[r]
            if below >= 0:
                self.higher[below] = above
            if above >= 0:
                self.lower[above] = below
            else:
                self.top = below

    def countInRoom(self, room):
        return self.count[room]

    def topPlayers(self, k):
        result = []
        r = self.top
        while r >= 0 and len(result) < k:
            p = self.head[r]
            while p >= 0 and len(result) < k:
                result.append(p)
                p = self.next[p]
            r = self.lower[r]
        return result


def solve(operation_names, argument_lists):
    if operation_names[0] != 'EscapeRoom' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = EscapeRoom(*argument_lists[0])
    allowed = {'advance', 'countInRoom', 'topPlayers'}
    voids = {'advance'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
