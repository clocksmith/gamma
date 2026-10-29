"""Hack2Hire 68b975348c4a0a9996afdd79 (Property Booking System) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class BookingSystem:
    def __init__(self, properties):
        self.free = {}  # neighborhood -> [(id, capacity)] sorted by id
        for pid, neighborhood, capacity in properties:
            self.free.setdefault(neighborhood, []).append((pid, int(capacity)))
        for props in self.free.values():
            props.sort()

    def book(self, neighborhood, groupSize):
        props = self.free.get(neighborhood, [])
        caps = sorted((c for _, c in props), reverse=True)
        size = total = 0
        while size < len(caps) and total < groupSize:
            total += caps[size]
            size += 1
        if total < groupSize:
            return []
        m, chosen, best = len(props), [], [None, None]

        def search(start, need, subtotal):
            if need == 0:
                if subtotal >= groupSize and (best[1] is None or subtotal < best[1]):
                    best[0], best[1] = list(chosen), subtotal
                return
            for i in range(start, m - need + 1):
                chosen.append(i)
                search(i + 1, need - 1, subtotal + props[i][1])
                chosen.pop()
        search(0, size, 0)
        picked = set(best[0])
        self.free[neighborhood] = [p for i, p in enumerate(props) if i not in picked]
        return [props[i][0] for i in best[0]]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'BookingSystem' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = BookingSystem(*argument_lists[0])
    allowed = {'book'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
