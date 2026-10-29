"""Hack2Hire 68d89bb279db2fbcd7d7db16 (Palindrome Stream Tracker) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class PalindromeStream:
    def __init__(self):
        # palindromic tree: node 0 has length -1, node 1 is the empty palindrome
        self.length = [-1, 0]
        self.link = [0, 0]
        self.edges = [{}, {}]
        self.chars = []
        self.last = 1

    def _extend_from(self, node, i, c):
        while True:
            j = i - 1 - self.length[node]
            if j >= 0 and self.chars[j] == c:
                return node
            node = self.link[node]

    def track(self, c):
        self.chars.append(c)
        i = len(self.chars) - 1
        node = self._extend_from(self.last, i, c)
        existing = self.edges[node].get(c)
        if existing is not None:
            self.last = existing
            return
        size = self.length[node] + 2
        if size == 1:
            suffix = 1
        else:
            suffix = self.edges[self._extend_from(self.link[node], i, c)][c]
        self.length.append(size)
        self.link.append(suffix)
        self.edges.append({})
        created = len(self.length) - 1
        self.edges[node][c] = created
        self.last = created

    def isPalindrome(self):
        return self.length[self.last] == len(self.chars)


def solve(operation_names, argument_lists):
    if operation_names[0] != 'PalindromeStream' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = PalindromeStream(*argument_lists[0])
    allowed = {'track', 'isPalindrome'}
    voids = {'track'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
