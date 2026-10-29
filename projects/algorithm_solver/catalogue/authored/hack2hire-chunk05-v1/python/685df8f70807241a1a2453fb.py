"""Original hack2hire:685df8f70807241a1a2453fb; inferred public-preview contract; qualification unknown."""
from collections import deque

class RateLimiter:
    def __init__(self, rules):
        self.rules = [(limit, window, deque()) for limit, window in rules]

    def allow(self, timestamp):
        allowed = True
        for limit, window, queue in self.rules:
            while queue and queue[0] <= timestamp - window:
                queue.popleft()
            if len(queue) >= limit:
                allowed = False
        if allowed:
            for limit, window, queue in self.rules:
                queue.append(timestamp)
        return allowed

def solve(operation_names, argument_lists):
    if len(operation_names) != len(argument_lists) or not operation_names or operation_names[0] != 'RateLimiter':
        raise ValueError("exact constructor trace required")
    instance = RateLimiter(*argument_lists[0])
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in ('allow',):
            raise ValueError("unknown method")
        result.append(getattr(instance, name)(*arguments))
    return result
