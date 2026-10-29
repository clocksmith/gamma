"""Hack2Hire 688aefae3867670cfb894129 (Oldest One-Time Visitor) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class VisitorTracker:
    def __init__(self):
        self.count = {}
        self.order = []  # usernames in order of their first login
        self.head = 0

    def login(self, username):
        seen = self.count.get(username, 0)
        if seen == 0:
            self.order.append(username)
        self.count[username] = seen + 1

    def getOldestOneTimeVisitor(self):
        while self.head < len(self.order) and self.count[self.order[self.head]] > 1:
            self.head += 1  # a repeat visitor never becomes a one-time visitor again
        return self.order[self.head] if self.head < len(self.order) else ''


def solve(operation_names, argument_lists):
    if operation_names[0] != 'VisitorTracker' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = VisitorTracker(*argument_lists[0])
    allowed = {'login', 'getOldestOneTimeVisitor'}
    voids = {'login'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
