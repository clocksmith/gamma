"""Hack2Hire 69c1e01c21f6ab4226964e08 (Roadway Segment Speed Query) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


SIZE = 1000002  # Fenwick indices 1 .. 1e6 + 1 for positions 0 .. 1e6


class RoadwaySpeedTracker:
    def __init__(self):
        self.sums = None
        self.counts = None
        self.live = {}

    def _update(self, position, speed, count):
        sums, counts = self.sums, self.counts
        i = position + 1
        while i < SIZE:
            sums[i] += speed
            counts[i] += count
            i += i & -i

    def addReport(self, start, end, speed):
        if self.sums is None:
            self.sums = [0] * SIZE
            self.counts = [0] * SIZE
        key = (start, end, speed)
        self.live[key] = self.live.get(key, 0) + 1
        self._update(start, speed, 1)
        self._update(end, -speed, -1)

    def removeReport(self, start, end, speed):
        key = (start, end, speed)
        copies = self.live.get(key, 0)
        if copies == 0:
            return False
        if copies == 1:
            del self.live[key]
        else:
            self.live[key] = copies - 1
        self._update(start, -speed, -1)
        self._update(end, speed, 1)
        return True

    def getAverageSpeed(self, point):
        if self.sums is None:
            return -1.0
        sums, counts = self.sums, self.counts
        total = 0
        count = 0
        i = point + 1
        while i > 0:
            total += sums[i]
            count += counts[i]
            i -= i & -i
        return total / count if count else -1.0


def solve(operation_names, argument_lists):
    if operation_names[0] != 'RoadwaySpeedTracker' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = RoadwaySpeedTracker(*argument_lists[0])
    allowed = {'addReport', 'removeReport', 'getAverageSpeed'}
    voids = {'addReport'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
