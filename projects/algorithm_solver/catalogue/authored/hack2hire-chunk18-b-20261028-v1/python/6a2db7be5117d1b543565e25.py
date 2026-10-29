"""Hack2Hire 6a2db7be5117d1b543565e25 (Design Durable Function Call Cache, variant 2 of 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""

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


def create_cache_key(function_name, bound):
    out = [str(len(function_name)) + ':' + function_name]
    _encode(bound, out)
    return ''.join(out)


class FunctionCallCache:
    def __init__(self, capacity, signatures):
        self.capacity = capacity
        self.signatures = {name: [list(p) for p in params] for name, params in signatures.items()}
        self.entries = OrderedDict()

    def call(self, functionName, args, kwargs):
        # bind positional, keyword and default arguments in parameter order
        bound = []
        for i, parameter in enumerate(self.signatures[functionName]):
            if i < len(args):
                bound.append(args[i])
            elif parameter[0] in kwargs:
                bound.append(kwargs[parameter[0]])
            else:
                bound.append(parameter[1])
        key = create_cache_key(functionName, bound)
        if key in self.entries:
            self.entries.move_to_end(key)
            return True
        self.entries[key] = True
        if len(self.entries) > self.capacity:
            self.entries.popitem(last=False)
        return False


def solve(operation_names, argument_lists):
    if operation_names[0] != 'FunctionCallCache' or len(argument_lists[0]) != 2:
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
