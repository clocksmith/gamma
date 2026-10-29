"""Original hack2hire:695d73139c1c1f40daea737f; inferred public-preview contract; qualification unknown."""
def _node():
    return {'edges': {}, 'terminal': False, 'value': None}

class RadixCache:
    def __init__(self):
        self.root = _node()

    def insert(self, sequence, value):
        key = list(sequence)
        node, position = self.root, 0
        while position < len(key):
            edge = node['edges'].get(key[position])
            if edge is None:
                leaf = _node()
                leaf.update(terminal=True, value=value)
                node['edges'][key[position]] = (key[position:], leaf)
                return
            label, child = edge
            common = 0
            while common < len(label) and position + common < len(key) and label[common] == key[position + common]:
                common += 1
            if common == len(label):
                node = child
                position += common
                continue
            middle = _node()
            middle['edges'][label[common]] = (label[common:], child)
            node['edges'][label[0]] = (label[:common], middle)
            position += common
            if position == len(key):
                middle.update(terminal=True, value=value)
            else:
                leaf = _node()
                leaf.update(terminal=True, value=value)
                middle['edges'][key[position]] = (key[position:], leaf)
            return
        node.update(terminal=True, value=value)

    def get(self, sequence):
        node, position = self.root, 0
        while position < len(sequence):
            edge = node['edges'].get(sequence[position])
            if edge is None:
                return None
            label, child = edge
            if list(sequence[position:position + len(label)]) != label:
                return None
            position += len(label)
            node = child
        return node['value'] if node['terminal'] else None

def solve(operation_names, argument_lists):
    if len(operation_names) != len(argument_lists) or not operation_names or operation_names[0] != 'RadixCache':
        raise ValueError("exact constructor trace required")
    instance = RadixCache(*argument_lists[0])
    result = [None]
    for name, arguments in zip(operation_names[1:], argument_lists[1:]):
        if name not in ('insert', 'get'):
            raise ValueError("unknown method")
        result.append(getattr(instance, name)(*arguments))
    return result
