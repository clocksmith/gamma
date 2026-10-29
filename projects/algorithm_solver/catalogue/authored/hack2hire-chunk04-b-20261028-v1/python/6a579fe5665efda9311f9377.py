"""Hack2Hire 6a579fe5665efda9311f9377 (Chat Message Events Aggregation, level 3) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""
from collections import deque


class ChatEventAggregator:
    def __init__(self, m):
        self.m = m
        self.users = {}
        self.chats = {}  # chatId -> [deque of (timestamp, userId), {userId: events in window}]

    def _trim_user(self, userId, timestamp):
        queue = self.users.get(userId)
        if queue is None:
            return 0
        low = timestamp - self.m + 1
        while queue and queue[0] < low:
            queue.popleft()
        if not queue:
            del self.users[userId]
            return 0
        return len(queue)

    def _trim_chat(self, chatId, timestamp):
        entry = self.chats.get(chatId)
        if entry is None:
            return None
        queue, multiplicity = entry
        low = timestamp - self.m + 1
        while queue and queue[0][0] < low:
            _, user = queue.popleft()
            left = multiplicity[user] - 1
            if left:
                multiplicity[user] = left
            else:
                del multiplicity[user]
        if not queue:
            del self.chats[chatId]
            return None
        return entry

    def recordEvent(self, timestamp, userId, chatId):
        queue = self.users.get(userId)
        if queue is None:
            queue = self.users[userId] = deque()
        queue.append(timestamp)
        self._trim_user(userId, timestamp)
        entry = self.chats.get(chatId)
        if entry is None:
            entry = self.chats[chatId] = [deque(), {}]
        entry[0].append((timestamp, userId))
        entry[1][userId] = entry[1].get(userId, 0) + 1
        self._trim_chat(chatId, timestamp)

    def getUserCount(self, timestamp, userId):
        return self._trim_user(userId, timestamp)

    def getChatCount(self, timestamp, chatId):
        entry = self._trim_chat(chatId, timestamp)
        return 0 if entry is None else len(entry[0])

    def getChatUserCount(self, timestamp, chatId):
        entry = self._trim_chat(chatId, timestamp)
        return 0 if entry is None else len(entry[1])


def solve(operation_names, argument_lists):
    if operation_names[0] != 'ChatEventAggregator' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = ChatEventAggregator(*argument_lists[0])
    allowed = {'recordEvent', 'getUserCount', 'getChatCount', 'getChatUserCount'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name == 'recordEvent' else value)
    return result
