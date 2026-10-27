"""211. Design Add and Search Words Data Structure."""
class WordDictionary:
    def __init__(self):
        self.root = {}

    def addWord(self, word: str) -> None:
        node = self.root
        for char in word:
            node = node.setdefault(char, {})
        node[''] = {}

    def search(self, word: str) -> bool:
        def visit(index: int, node: dict) -> bool:
            if index == len(word):
                return '' in node
            char = word[index]
            if char == '.':
                return any(key and visit(index + 1, child) for key, child in node.items())
            return char in node and visit(index + 1, node[char])
        return visit(0, self.root)

def solve(operations: list[str], arguments: list[list[str]]) -> list:
    dictionary = WordDictionary()
    result = []
    for operation, values in zip(operations, arguments):
        if operation == 'WordDictionary':
            result.append(None)
        else:
            result.append(getattr(dictionary, operation)(*values))
    return result
