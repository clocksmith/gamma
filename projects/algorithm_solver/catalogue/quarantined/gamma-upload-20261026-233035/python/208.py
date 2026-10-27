"""208. Implement Trie (Prefix Tree)."""
class Trie:
    def __init__(self):
        self.root = {}

    def insert(self, word: str) -> None:
        node = self.root
        for char in word:
            node = node.setdefault(char, {})
        node[''] = {}

    def search(self, word: str) -> bool:
        node = self.root
        for char in word:
            if char not in node:
                return False
            node = node[char]
        return '' in node

    def startsWith(self, prefix: str) -> bool:
        node = self.root
        for char in prefix:
            if char not in node:
                return False
            node = node[char]
        return True

def solve(operations: list[str], arguments: list[list[str]]) -> list:
    trie = Trie()
    result = []
    for operation, values in zip(operations, arguments):
        if operation == 'Trie':
            result.append(None)
        else:
            result.append(getattr(trie, operation)(*values))
    return result
