"""Hack2Hire 68799c22ef2889afac734164 (Food Delivery System, variant 1 of 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class FoodDeliverySystem:
    def __init__(self, restaurants, menu):
        location = {rid: (x, y) for rid, x, y in restaurants}
        self.cheapest = {}
        self.xs = {}  # item -> x coordinates of the restaurants offering it
        self.ys = {}  # item -> matching y coordinates
        for rid, item, price in menu:
            if item not in self.cheapest or price < self.cheapest[item]:
                self.cheapest[item] = price
            x, y = location[rid]
            self.xs.setdefault(item, []).append(x)
            self.ys.setdefault(item, []).append(y)

    def getBestOption(self, item, userX, userY):
        xs = self.xs.get(item)
        if xs is None:
            return [-1, -1]
        fastest = min(abs(x - userX) + abs(y - userY) for x, y in zip(xs, self.ys[item]))
        return [self.cheapest[item], fastest]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'FoodDeliverySystem' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = FoodDeliverySystem(*argument_lists[0])
    allowed = {'getBestOption'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
