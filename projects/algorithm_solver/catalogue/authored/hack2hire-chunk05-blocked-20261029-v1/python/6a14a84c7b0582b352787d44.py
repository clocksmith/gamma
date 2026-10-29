"""Hack2Hire 6a14a84c7b0582b352787d44 (Design Ambient Light Sensor System) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.

Sequential only: the inferred thread-safe, non-blocking contract is not modelled here."""

SLOTS = 1000001  # timestamps 0..1e6


class ALSWrapper:
    def __init__(self):
        self.counts = {}
        self.sums = {}
        self.latest = None

    def record(self, status, lux, timestamp):
        if status != 1:
            return
        i = timestamp + 1
        while i <= SLOTS:
            self.counts[i] = self.counts.get(i, 0) + 1
            self.sums[i] = self.sums.get(i, 0) + lux
            i += i & -i
        if self.latest is None or timestamp >= self.latest[0]:
            self.latest = (timestamp, lux)

    def _prefix(self, i):
        count = total = 0
        while i > 0:
            count += self.counts.get(i, 0)
            total += self.sums.get(i, 0)
            i -= i & -i
        return count, total

    def getLatestLux(self):
        return -1 if self.latest is None else self.latest[1]

    def getAverageLux(self, startTime, endTime):
        high_count, high_total = self._prefix(endTime + 1)
        low_count, low_total = self._prefix(startTime)
        count = high_count - low_count
        if count == 0:
            return -1
        return (high_total - low_total) // count


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ALSWrapper' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = ALSWrapper()
    allowed = {'record', 'getLatestLux', 'getAverageLux'}
    voids = {'record'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
