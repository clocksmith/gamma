"""Hack2Hire 683e86418d3dfb7c9bd756ab (Design Unix Find Command, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


def _leaf(spec):
    kind, operand = spec
    if kind == 'sizeGreaterThan':
        return lambda name, size: size > operand
    if kind == 'extension':
        return lambda name, size: (name.rsplit('.', 1)[1] if '.' in name else '') == operand
    if kind == 'namePrefix':
        return lambda name, size: name.startswith(operand)
    raise ValueError('unknown filter')


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
        tests = [_leaf(spec) for spec in filters]
        accept = lambda name, size: all(test(name, size) for test in tests)
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
