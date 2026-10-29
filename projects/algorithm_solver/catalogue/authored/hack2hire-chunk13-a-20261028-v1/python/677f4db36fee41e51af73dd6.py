"""Hack2Hire 677f4db36fee41e51af73dd6 (Persistent Stack) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class PStack:
    def __init__(self):
        # version v is the top node of a shared singly linked list; node 0 is the empty stack
        self.parent = [0]
        self.value = [0]
        self.length = [0]

    def push(self, version, val):
        self.parent.append(version)
        self.value.append(val)
        self.length.append(self.length[version] + 1)
        return len(self.parent) - 1

    def pop(self, version):
        return self.parent[version]

    def peek(self, version):
        return self.value[version]

    def size(self, version):
        return self.length[version]


def solve(operation_names, argument_lists):
    if operation_names[0] != 'PStack' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = PStack(*argument_lists[0])
    allowed = {'push', 'pop', 'peek', 'size'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
