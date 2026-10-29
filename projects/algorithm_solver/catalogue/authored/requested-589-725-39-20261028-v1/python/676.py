"""Original LeetCode 676 candidate; qualification unknown."""

class MagicDictionary:
    def __init__(self): self.patterns = {}
    def buildDict(self, dictionary):
        self.patterns = {}
        for word in dictionary:
            for i, c in enumerate(word):
                pattern = word[:i] + '*' + word[i+1:]
                self.patterns[pattern] = self.patterns.get(pattern, 0) | (1 << (ord(c) - 97))
    def search(self, searchWord):
        for i, c in enumerate(searchWord):
            pattern = searchWord[:i] + '*' + searchWord[i+1:]
            if self.patterns.get(pattern, 0) & ~(1 << (ord(c) - 97)): return True
        return False


def solve(operations, arguments):
    instance = MagicDictionary(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result
