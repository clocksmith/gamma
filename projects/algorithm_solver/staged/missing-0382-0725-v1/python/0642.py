"""642. Design Search Autocomplete System."""

class _TrieNode:
    def __init__(self):
        self.children = {}
        self.top = []


class AutocompleteSystem:
    def __init__(self, sentences: list[str], times: list[int]):
        self.root = _TrieNode()
        self.frequency = {}
        self.prefix = ''
        self.cursor = self.root
        for sentence, count in zip(sentences, times):
            self._record(sentence, count)

    def _record(self, sentence, count):
        self.frequency[sentence] = self.frequency.get(sentence, 0) + count
        node = self.root
        for char in sentence:
            if char not in node.children:
                node.children[char] = _TrieNode()
            node = node.children[char]
            if sentence not in node.top:
                node.top.append(sentence)
            node.top.sort(key=lambda text: (-self.frequency[text], text))
            del node.top[3:]

    def input(self, c: str) -> list[str]:
        if c == '#':
            if self.prefix:
                self._record(self.prefix, 1)
            self.prefix = ''
            self.cursor = self.root
            return []
        self.prefix += c
        if self.cursor is not None:
            self.cursor = self.cursor.children.get(c)
        return [] if self.cursor is None else self.cursor.top[:]


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = AutocompleteSystem(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = AutocompleteSystem
