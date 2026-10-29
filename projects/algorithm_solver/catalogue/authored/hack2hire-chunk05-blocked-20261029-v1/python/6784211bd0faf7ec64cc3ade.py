"""Hack2Hire 6784211bd0faf7ec64cc3ade (Design Card Game, variant 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class CardGame:
    def __init__(self, deck):
        self.deck = list(deck)
        self.position = 0
        self.scores = {'A': 0, 'B': 0}

    def playRound(self):
        if self.position + 2 > len(self.deck):
            return ''
        a, b = self.deck[self.position], self.deck[self.position + 1]
        self.position += 2
        rank_a, rank_b = a % 13, b % 13
        if rank_a == rank_b:
            return 'TIE'
        winner = 'A' if rank_a > rank_b else 'B'
        self.scores[winner] += rank_a + rank_b + 2
        return winner

    def getScore(self, player):
        return self.scores[player]

    def getWinner(self):
        if self.position < len(self.deck):
            return ''
        a, b = self.scores['A'], self.scores['B']
        return 'TIE' if a == b else ('A' if a > b else 'B')


def solve(operation_names, argument_lists):
    if operation_names[0] != 'CardGame' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = CardGame(*argument_lists[0])
    allowed = {'playRound', 'getScore', 'getWinner'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
