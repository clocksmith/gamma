"""Hack2Hire 6920d01494b324049c3251bd (Design KV Store with Rollback, variant 1 of 3) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class KeyValueStore:
    def __init__(self):
        self.data = {}

    def set(self, key, value):
        self.data[key] = value

    def get(self, key):
        return self.data.get(key, '')

    def unset(self, key):
        self.data.pop(key, None)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'KeyValueStore' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = KeyValueStore(*argument_lists[0])
    allowed = {'set', 'get', 'unset'}
    voids = {'set', 'unset'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
