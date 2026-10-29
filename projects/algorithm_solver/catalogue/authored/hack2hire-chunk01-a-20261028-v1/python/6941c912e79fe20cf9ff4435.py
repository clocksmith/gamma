"""Hack2Hire 6941c912e79fe20cf9ff4435 (Design Tennis Game, variant 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

CALLS = ('Love', '15', '30', '40')


class TennisSet:
    def __init__(self):
        self.games = [0, 0]
        self.points = [0, 0]
        self.tiebreak = False
        self.winner = ''

    def pointTo(self, player):
        if self.winner:
            return
        me = 0 if player == 'A' else 1
        self.points[me] += 1
        need = 7 if self.tiebreak else 4
        if self.points[me] < need or self.points[me] - self.points[1 - me] < 2:
            return
        self.points = [0, 0]
        self.games[me] += 1
        if self.tiebreak or (self.games[me] >= 6 and self.games[me] - self.games[1 - me] >= 2):
            self.winner = player
            self.tiebreak = False
        elif self.games == [6, 6]:
            self.tiebreak = True

    def getGames(self):
        return list(self.games)

    def getGameScore(self):
        if self.winner:
            return 'Set ' + self.winner
        a, b = self.points
        if self.tiebreak:
            return 'Tiebreak %d-%d' % (a, b)
        if a >= 3 and b >= 3:
            return 'Deuce' if a == b else 'Advantage ' + ('A' if a > b else 'B')
        return CALLS[a] + '-' + CALLS[b]

    def getWinner(self):
        return self.winner


def solve(operation_names, argument_lists):
    if operation_names[0] != 'TennisSet' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = TennisSet()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in ('pointTo', 'getGames', 'getGameScore', 'getWinner'):
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
