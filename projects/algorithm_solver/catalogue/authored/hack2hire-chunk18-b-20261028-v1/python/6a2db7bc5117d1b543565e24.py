"""Hack2Hire 6a2db7bc5117d1b543565e24 (Design Durable Function Call Cache, variant 1 of 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

from collections import OrderedDict


def _encode(value, out):
    # type-tagged, self-delimiting serialisation; object keys in sorted order
    if value is None:
        out.append('n')
    elif value is True:
        out.append('T')
    elif value is False:
        out.append('F')
    elif type(value) is int:
        out.append('i' + str(value) + ';')
    elif type(value) is str:
        out.append('s' + str(len(value)) + ':' + value)
    elif type(value) is list:
        out.append('[')
        for item in value:
            _encode(item, out)
        out.append(']')
    else:
        out.append('{')
        for key in sorted(value):
            out.append(str(len(key)) + ':' + key)
            _encode(value[key], out)
        out.append('}')


def create_cache_key(function_name, args, kwargs):
    out = [str(len(function_name)) + ':' + function_name]
    _encode(args, out)
    _encode(kwargs, out)
    return ''.join(out)


class FunctionCallCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.entries = OrderedDict()

    def call(self, functionName, args, kwargs):
        key = create_cache_key(functionName, args, kwargs)
        if key in self.entries:
            self.entries.move_to_end(key)
            return True
        self.entries[key] = True
        if len(self.entries) > self.capacity:
            self.entries.popitem(last=False)
        return False


def solve(operation_names, argument_lists):
    if operation_names[0] != 'FunctionCallCache' or len(argument_lists[0]) != 1:
        raise ValueError('exact initial constructor required')
    instance = FunctionCallCache(*argument_lists[0])
    allowed = {'call'}
    voids = set()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
