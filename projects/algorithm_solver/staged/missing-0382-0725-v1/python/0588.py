"""588. Design In-Memory File System."""

class _Entry:
    def __init__(self):
        self.children = {}
        self.is_file = False
        self.parts = []


class FileSystem:
    def __init__(self):
        self.root = _Entry()

    def _lookup(self, path, create=False):
        node = self.root
        for name in path.split('/'):
            if not name:
                continue
            if create and name not in node.children:
                node.children[name] = _Entry()
            node = node.children[name]
        return node

    def ls(self, path: str) -> list[str]:
        node = self._lookup(path)
        return [path.rsplit('/', 1)[-1]] if node.is_file else sorted(node.children)

    def mkdir(self, path: str) -> None:
        self._lookup(path, True)

    def addContentToFile(self, filePath: str, content: str) -> None:
        node = self._lookup(filePath, True)
        node.is_file = True
        node.parts.append(content)

    def readContentFromFile(self, filePath: str) -> str:
        return ''.join(self._lookup(filePath).parts)


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = FileSystem(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = FileSystem
