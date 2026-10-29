"""Hack2Hire 6a579fe4665efda9311f9376 (Chat Message Events Aggregation, level 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""
from collections import deque


class ChatEventAggregator:
    def __init__(self, m):
        self.m = m
        self.users = {}
        self.chats = {}

    def _trim(self, queue, timestamp):
        low = timestamp - self.m + 1
        while queue and queue[0] < low:
            queue.popleft()

    def _count(self, table, key, timestamp):
        queue = table.get(key)
        if queue is None:
            return 0
        self._trim(queue, timestamp)
        if not queue:
            del table[key]
            return 0
        return len(queue)

    def recordEvent(self, timestamp, userId, chatId):
        for table, key in ((self.users, userId), (self.chats, chatId)):
            queue = table.get(key)
            if queue is None:
                queue = table[key] = deque()
            queue.append(timestamp)
            self._trim(queue, timestamp)

    def getUserCount(self, timestamp, userId):
        return self._count(self.users, userId, timestamp)

    def getChatCount(self, timestamp, chatId):
        return self._count(self.chats, chatId, timestamp)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ChatEventAggregator' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = ChatEventAggregator(*argument_lists[0])
    allowed = {'recordEvent', 'getUserCount', 'getChatCount'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name == 'recordEvent' else value)
    return result
