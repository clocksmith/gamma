"""Original hack2hire:680e4d4d7003ce5d1dcb037e; inferred public-preview contract; qualification unknown."""
from collections import OrderedDict
from copy import deepcopy

class LRUCache:
    def __init__(self, capacity):
        self.capacity = capacity
        self.values = OrderedDict()

    def _evict(self):
        while len(self.values) > self.capacity:
            self.values.popitem(last=False)

    def get(self, key):
        if key not in self.values:
            return -1
        self.values.move_to_end(key)
        return deepcopy(self.values[key])

    def put(self, key, value):
        self.values[key] = deepcopy(value)
        self.values.move_to_end(key)
        self._evict()

    def resize(self, capacity):
        self.capacity = capacity
        self._evict()

def solve(operation_names, argument_lists):
    if len(operation_names) != len(argument_lists) or not operation_names or operation_names[0] != 'LRUCache':
        raise ValueError("exact constructor trace required")
    instance = LRUCache(*argument_lists[0])
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in ('get', 'put', 'resize'):
            raise ValueError("unknown method")
        result.append(getattr(instance, name)(*arguments))
    return result
