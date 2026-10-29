"""Hack2Hire 6a579fe2665efda9311f9375 (Chat Message Events Aggregation, level 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""
from collections import deque


class ChatEventAggregator:
    def __init__(self, m):
        self.m = m
        self.users = {}

    def _trim(self, queue, timestamp):
        low = timestamp - self.m + 1
        while queue and queue[0] < low:
            queue.popleft()

    def recordEvent(self, timestamp, userId, chatId):
        queue = self.users.get(userId)
        if queue is None:
            queue = self.users[userId] = deque()
        queue.append(timestamp)
        self._trim(queue, timestamp)

    def getUserCount(self, timestamp, userId):
        queue = self.users.get(userId)
        if queue is None:
            return 0
        self._trim(queue, timestamp)
        if not queue:
            del self.users[userId]
            return 0
        return len(queue)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ChatEventAggregator' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = ChatEventAggregator(*argument_lists[0])
    allowed = {'recordEvent', 'getUserCount'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name == 'recordEvent' else value)
    return result
