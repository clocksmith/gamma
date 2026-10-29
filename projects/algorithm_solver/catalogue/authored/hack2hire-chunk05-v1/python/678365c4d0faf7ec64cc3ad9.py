"""Original hack2hire:678365c4d0faf7ec64cc3ad9; inferred public-preview contract; qualification unknown."""
class PathKeyValueStore:
    def __init__(self):
        self.values = {'/': 'root'}
        self.children = {'/': 0}

    def create(self, path, value):
        parent = path.rsplit('/', 1)[0] or '/'
        if path in self.values or parent not in self.values:
            return False
        self.values[path] = value
        self.children[path] = 0
        self.children[parent] += 1
        return True

    def set(self, path, value):
        if path == '/' or path not in self.values:
            return False
        self.values[path] = value
        return True

    def get(self, path):
        return self.values.get(path)

    def delete(self, path):
        if path == '/' or path not in self.values or self.children[path]:
            return False
        parent = path.rsplit('/', 1)[0] or '/'
        self.children[parent] -= 1
        del self.values[path]
        del self.children[path]
        return True

def solve(operation_names, argument_lists):
    if len(operation_names) != len(argument_lists) or not operation_names or operation_names[0] != 'PathKeyValueStore':
        raise ValueError("exact constructor trace required")
    instance = PathKeyValueStore(*argument_lists[0])
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in ('create', 'set', 'get', 'delete'):
            raise ValueError("unknown method")
        result.append(getattr(instance, name)(*arguments))
    return result
