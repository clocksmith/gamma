"""Hack2Hire 68edc9c15abdefad4f6693fc (Event Logger with Rate Limiting) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class EventLogger:
    def __init__(self, window):
        self.window = window
        self.last = {}

    def logEvent(self, name, timestamp):
        previous = self.last.get(name)
        if previous is not None and timestamp - previous < self.window:
            return False
        self.last[name] = timestamp
        return True


def solve(operation_names, argument_lists):
    if operation_names[0] != 'EventLogger' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = EventLogger(*argument_lists[0])
    allowed = {'logEvent'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
