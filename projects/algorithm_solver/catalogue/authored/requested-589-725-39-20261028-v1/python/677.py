"""Original LeetCode 677 candidate; qualification unknown."""

class MapSum:
    def __init__(self): self.values, self.root = {}, {'sum': 0, 'children': {}}
    def insert(self, key, val):
        delta = val - self.values.get(key, 0)
        self.values[key] = val
        node = self.root
        node['sum'] += delta
        for c in key:
            if c not in node['children']: node['children'][c] = {'sum': 0, 'children': {}}
            node = node['children'][c]
            node['sum'] += delta
    def sum(self, prefix):
        node = self.root
        for c in prefix:
            node = node['children'].get(c)
            if node is None: return 0
        return node['sum']


def solve(operations, arguments):
    instance = MapSum(*arguments[0])
    result = [None]
    for operation, values in zip(operations[1:], arguments[1:]):
        result.append(getattr(instance, operation)(*values))
    return result
