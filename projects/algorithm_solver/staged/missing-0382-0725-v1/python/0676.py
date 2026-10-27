"""676. Implement Magic Dictionary."""

class MagicDictionary:
    def __init__(self):
        self.patterns = {}

    def buildDict(self, dictionary: list[str]) -> None:
        self.patterns.clear()
        for word in dictionary:
            for i, char in enumerate(word):
                pattern = word[:i] + '*' + word[i + 1:]
                self.patterns.setdefault(pattern, set()).add(char)

    def search(self, searchWord: str) -> bool:
        for i, char in enumerate(searchWord):
            pattern = searchWord[:i] + '*' + searchWord[i + 1:]
            values = self.patterns.get(pattern)
            if values and (len(values) > 1 or char not in values):
                return True
        return False


def solve(operations: list[str], arguments: list[list]) -> list:
    """Replay native operations on one request-local instance."""
    if not operations:
        return []
    instance = MagicDictionary(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result


Solution = MagicDictionary
