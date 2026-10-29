"""Hack2Hire 694609632c048134ada83559 (Design Dual Circuit Breakers) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class _Breaker:
    def __init__(self, threshold, cooldown):
        self.threshold = threshold
        self.cooldown = cooldown
        self.is_open = False
        self.opened = 0
        self.failures = 0

    def allows(self, t):
        return not self.is_open or t - self.opened >= self.cooldown

    def report(self, t, ok):
        if ok:
            self.is_open = False
            self.failures = 0
        elif self.is_open:
            self.opened = t
        else:
            self.failures += 1
            if self.failures >= self.threshold:
                self.is_open = True
                self.opened = t
                self.failures = 0


class DualCircuitBreaker:
    def __init__(self, failureThreshold, cooldown):
        self.primary = _Breaker(failureThreshold, cooldown)
        self.secondary = _Breaker(failureThreshold, cooldown)

    def request(self, timestamp, primaryOk, secondaryOk):
        attempted = False
        if self.primary.allows(timestamp):
            attempted = True
            self.primary.report(timestamp, primaryOk)
            if primaryOk:
                return 'PRIMARY'
        if self.secondary.allows(timestamp):
            self.secondary.report(timestamp, secondaryOk)
            return 'SECONDARY' if secondaryOk else 'FAILED'
        return 'FAILED' if attempted else 'BLOCKED'


def solve(operation_names, argument_lists):
    if operation_names[0] != 'DualCircuitBreaker' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = DualCircuitBreaker(*argument_lists[0])
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name != 'request':
            raise ValueError('unknown method')
        result.append(instance.request(*arguments))
    return result
