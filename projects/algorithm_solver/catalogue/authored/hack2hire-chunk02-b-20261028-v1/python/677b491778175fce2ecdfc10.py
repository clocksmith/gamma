"""Original Hack2Hire 677b491778175fce2ecdfc10 native class variant over an INFERRED specification, with a separately declared trace adapter; qualification unknown."""


class FunctionLibrary:
    def __init__(self):
        self.exact = {}
        self.variadic = {}

    def register(self, name, argumentTypes, isVariadic):
        table = self.variadic if isVariadic else self.exact
        table.setdefault(tuple(argumentTypes), []).append(name)

    def findMatches(self, argumentTypes):
        args = tuple(argumentTypes)
        found = list(self.exact.get(args, ()))
        if args:
            start = len(args) - 1
            while start > 0 and args[start - 1] == args[-1]:
                start -= 1
            for k in range(start + 1, len(args) + 1):
                found.extend(self.variadic.get(args[:k], ()))
        return sorted(found)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'FunctionLibrary' or argument_lists[0] != []:
        raise ValueError('exact initial constructor required')
    instance, result = FunctionLibrary(), [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in ('register', 'findMatches'):
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
