"""Hack2Hire 6941be52b9d646bec48c68cc (Design Tennis Game, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

CALLS = ('Love', '15', '30', '40')


class TennisGame:
    def __init__(self):
        self.points = [0, 0]
        self.winner = ''

    def pointTo(self, player):
        if self.winner:
            return
        me = 0 if player == 'A' else 1
        self.points[me] += 1
        if self.points[me] >= 4 and self.points[me] - self.points[1 - me] >= 2:
            self.winner = player

    def getPoints(self):
        return list(self.points)

    def getScore(self):
        a, b = self.points
        if self.winner:
            return 'Game ' + self.winner
        if a >= 3 and b >= 3:
            return 'Deuce' if a == b else 'Advantage ' + ('A' if a > b else 'B')
        return CALLS[a] + '-' + CALLS[b]

    def getWinner(self):
        return self.winner


def solve(operation_names, argument_lists):
    if operation_names[0] != 'TennisGame' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = TennisGame()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in ('pointTo', 'getPoints', 'getScore', 'getWinner'):
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
