"""Hack2Hire 683f1dc68d3dfb7c9bd756da (Design Unix Find Command, variant 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


def _leaf(spec):
    kind, operand = spec
    if kind == 'sizeGreaterThan':
        return lambda name, size: size > operand
    if kind == 'extension':
        return lambda name, size: (name.rsplit('.', 1)[1] if '.' in name else '') == operand
    if kind == 'namePrefix':
        return lambda name, size: name.startswith(operand)
    raise ValueError('unknown filter')


def _compile(spec):
    kind = spec[0]
    if kind in ('and', 'or'):
        parts = [_compile(part) for part in spec[1]]
        if kind == 'and':
            return lambda name, size: all(part(name, size) for part in parts)
        return lambda name, size: any(part(name, size) for part in parts)
    if kind == 'not':
        inner = _compile(spec[1])
        return lambda name, size: not inner(name, size)
    return _leaf(spec)


class _Directory:
    __slots__ = ('directories', 'files')

    def __init__(self):
        self.directories = {}
        self.files = {}


class FileSystem:
    def __init__(self):
        self.root = _Directory()

    def addFile(self, path, size):
        parts = path.split('/')[1:]
        node = self.root
        for part in parts[:-1]:
            node = node.directories.setdefault(part, _Directory())
        node.files[parts[-1]] = (size, path)  # full path kept so queries do not rebuild it

    def find(self, directory, filters):
        accept = _compile(filters)
        node = self.root
        if directory != '/':
            for part in directory.split('/')[1:]:
                node = node.directories.get(part)
                if node is None:
                    return []
        found = []
        stack = [node]
        while stack:
            current = stack.pop()
            for name, (size, full) in current.files.items():
                if accept(name, size):
                    found.append(full)
            stack.extend(current.directories.values())
        found.sort()
        return found


def solve(operation_names, argument_lists):
    if operation_names[0] != 'FileSystem' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = FileSystem()
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in ('addFile', 'find'):
            raise ValueError('unknown method')
        result.append(getattr(instance, name)(*arguments))
    return result
