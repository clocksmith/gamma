"""Hack2Hire 6879a663ef2889afac734167 (Food Delivery System, variant 2 of 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


def _fastest(xs, ys, userX, userY):
    return min(abs(x - userX) + abs(y - userY) for x, y in zip(xs, ys))


class FoodDeliverySystem:
    def __init__(self, restaurants, menu):
        self.location = {rid: (x, y) for rid, x, y in restaurants}
        self.cheapest = {}
        self.offers = {}  # item -> {restaurant id: price}
        self.xs = {}      # item -> x coordinates of the restaurants offering it
        self.ys = {}
        for rid, item, price in menu:
            if item not in self.cheapest or price < self.cheapest[item]:
                self.cheapest[item] = price
            self.offers.setdefault(item, {})[rid] = price
            x, y = self.location[rid]
            self.xs.setdefault(item, []).append(x)
            self.ys.setdefault(item, []).append(y)
        self.orders = {}  # sorted item tuple -> (lowest total, xs, ys) of qualifying restaurants; the menu never changes

    def getBestOption(self, item, userX, userY):
        xs = self.xs.get(item)
        if xs is None:
            return [-1, -1]
        return [self.cheapest[item], _fastest(xs, self.ys[item], userX, userY)]

    def _order(self, items):
        maps = []
        for item in items:
            offers = self.offers.get(item)
            if offers is None:
                return None
            maps.append(offers)
        rarest = min(maps, key=len)
        best, xs, ys = -1, [], []
        for rid in rarest:
            total = 0
            for offers in maps:
                price = offers.get(rid)
                if price is None:
                    break
                total += price
            else:
                if best < 0 or total < best:
                    best = total
                x, y = self.location[rid]
                xs.append(x)
                ys.append(y)
        return (best, xs, ys) if xs else None

    def getBestOrder(self, items, userX, userY):
        key = tuple(sorted(items))
        if key not in self.orders:
            self.orders[key] = self._order(items)
        found = self.orders[key]
        if found is None:
            return [-1, -1]
        return [found[0], _fastest(found[1], found[2], userX, userY)]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'FoodDeliverySystem' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = FoodDeliverySystem(*argument_lists[0])
    allowed = {'getBestOption', 'getBestOrder'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
