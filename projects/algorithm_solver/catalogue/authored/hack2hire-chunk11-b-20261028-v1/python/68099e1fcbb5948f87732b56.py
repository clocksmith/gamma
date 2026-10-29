"""Hack2Hire 68099e1fcbb5948f87732b56 (KV Store with Prefix Search) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown."""


class KVStore:
    def __init__(self):
        self.values = {}
        self.root = [{}, 0, False]  # trie node: [children by letter, live keys below, key ends here]

    def set(self, key, value):
        self.values[key] = value
        node = self.root
        node[1] += 1
        for ch in key:
            child = node[0].get(ch)
            if child is None:
                child = node[0][ch] = [{}, 0, False]
            child[1] += 1
            node = child
        node[2] = True

    def get(self, key):
        return self.values.get(key, -1)

    def update(self, key, value):
        self.values[key] = value

    def deleteKey(self, key):
        if key not in self.values:
            return
        del self.values[key]
        node = self.root
        node[1] -= 1
        for ch in key:
            child = node[0][ch]
            child[1] -= 1
            if child[1] == 0:
                del node[0][ch]  # prune the now-empty branch
                return
            node = child
        node[2] = False

    def prefixSearch(self, prefix):
        node = self.root
        for ch in prefix:
            node = node[0].get(ch)
            if node is None:
                return []
        out = []
        stack = [(node, prefix)]
        while stack:
            node, path = stack.pop()
            if node[2]:
                out.append(self.values[path])
            for ch in sorted(node[0], reverse=True):
                stack.append((node[0][ch], path + ch))
        return out


def solve(operation_names, argument_lists):
    if operation_names[0] != 'KVStore' or len(argument_lists[0]) != 0:
        raise ValueError('exact initial constructor required')
    instance = KVStore(*argument_lists[0])
    allowed = {'set', 'get', 'update', 'deleteKey', 'prefixSearch'}
    voids = {'set', 'update', 'deleteKey'}
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in allowed:
            raise ValueError('unknown method')
        value = getattr(instance, name)(*arguments)
        result.append(None if name in voids else value)
    return result
