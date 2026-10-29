"""Hack2Hire 6a7a3b72d713d873ca7aaf62 (Apply Domain Request Limits) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from collections import deque


class DomainRateLimiter:
    def __init__(self, maxRequests, windowSize):
        self.limit = maxRequests
        self.window = windowSize
        self.clock = 0
        self.accepted = {}

    def allowRequest(self, domain):
        self.clock += 1
        times = self.accepted.get(domain)
        if times is None:
            times = deque()
            self.accepted[domain] = times
        oldest = self.clock - self.window
        while times and times[0] <= oldest:
            times.popleft()
        if len(times) < self.limit:
            times.append(self.clock)
            return True
        return False


def solve(operation_names, argument_lists):
    if operation_names[0] != 'DomainRateLimiter' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = DomainRateLimiter(*argument_lists[0])
    allowed = {'allowRequest'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
