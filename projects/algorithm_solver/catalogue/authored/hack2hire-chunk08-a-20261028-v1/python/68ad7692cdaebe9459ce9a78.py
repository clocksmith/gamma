"""Hack2Hire 68ad7692cdaebe9459ce9a78 (Realtime Bot IP Detection) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from collections import deque


class DetectionSystem:
    def __init__(self, maxRequests, windowSeconds):
        self.limit = maxRequests
        self.window = windowSeconds
        self.recent = {}

    def isBot(self, ip, timestamp):
        queue = self.recent.get(ip)
        if queue is None:
            queue = self.recent[ip] = deque()
        queue.append(timestamp)
        low = timestamp - self.window + 1
        while queue[0] < low:
            queue.popleft()
        return len(queue) > self.limit


def solve(operation_names, argument_lists):
    if operation_names[0] != 'DetectionSystem' or len(argument_lists[0]) != 2:
        raise ValueError('exact initial constructor required')
    instance = DetectionSystem(*argument_lists[0])
    allowed = {'isBot'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
