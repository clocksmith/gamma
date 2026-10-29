"""Original candidate; no qualification or admission."""

from collections import deque

class StreamChecker:
    def __init__(self,words):
        self.root={};self.limit=max(map(len,words));self.stream=deque(maxlen=self.limit)
        for word in words:
            node=self.root
            for c in reversed(word):node=node.setdefault(c,{})
            node['!']=True
    def query(self,letter):
        self.stream.append(letter);node=self.root
        for c in reversed(self.stream):
            if c not in node:return False
            node=node[c]
            if '!' in node:return True
        return False


def solve(operations, arguments):
    instance = StreamChecker(*arguments[0])
    out = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        out.append(getattr(instance, operation)(*values))
    return out
