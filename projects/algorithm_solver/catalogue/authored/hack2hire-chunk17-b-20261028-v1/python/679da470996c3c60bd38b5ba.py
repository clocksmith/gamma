"""Hack2Hire 679da470996c3c60bd38b5ba (Alien Base Attack) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class AlienBaseAttack:
    def __init__(self, n):
        self.n = n
        self.destroyed = set()

    def attack(self, x):
        if 0 <= x < self.n:
            self.destroyed.add(x)

    def isDestroyed(self):
        return len(self.destroyed) == self.n


def solve(operation_names, argument_lists):
    if operation_names[0] != 'AlienBaseAttack' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = AlienBaseAttack(*argument_lists[0])
    allowed = {'attack', 'isDestroyed'}
    voids = {'attack'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
