"""Untrusted-process transport. Contains no expected outputs or verdicts."""
import json
import math
import sys

class ListNode:
    def __init__(self, val=0, next=None):
        self.val, self.next = val, next

class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val, self.left, self.right = val, left, right

def decode(value):
    if type(value) is list:
        return [decode(x) for x in value]
    if type(value) is not dict:
        return value
    if set(value) == {'__gamma_bigint_v1__'}:
        return int(value['__gamma_bigint_v1__'])
    if set(value) == {'__list_node__'}:
        head = None
        for x in reversed(value['__list_node__']):
            head = ListNode(decode(x), head)
        return head
    if set(value) == {'__tree_node__'}:
        a = value['__tree_node__']
        if not a or a[0] is None:
            return None
        root = TreeNode(decode(a[0])); queue = [root]; index = 1
        for node in queue:
            for key in ('left', 'right'):
                if index < len(a) and a[index] is not None:
                    child = TreeNode(decode(a[index])); setattr(node, key, child); queue.append(child)
                index += 1
        return root
    return {k: decode(v) for k, v in value.items()}

def fields(value):
    if type(value) is list:
        return list(enumerate(value))
    if type(value) is dict:
        if any(type(k) is not str for k in value):
            raise TypeError('non-string dictionary key')
        return list(value.items())
    data = vars(value)
    if set(data) == {'val', 'next'}:
        return [(k, data[k]) for k in ('val', 'next')]
    if set(data) == {'val', 'left', 'right'}:
        return [(k, data[k]) for k in ('val', 'left', 'right')]
    raise TypeError('unsupported object shape')

def encode(value, active=None):
    active = set() if active is None else active
    if value is None or type(value) in (str, bool):
        return value
    if type(value) is int:
        return {'__gamma_bigint_v1__': str(value)} if abs(value) > 2**53-1 else value
    if type(value) is float:
        if not math.isfinite(value) or (value.is_integer() and abs(value) > 2**53-1):
            raise ValueError('unsafe floating point output')
        return value
    if id(value) in active:
        raise ValueError('cyclic output')
    active = active | {id(value)}
    if type(value) is list:
        return [encode(x, active) for x in value]
    if type(value) is dict:
        return {k: encode(v, active) for k, v in fields(value)}
    data = dict(fields(value))
    if 'next' in data:
        result = []; seen = set(); node = value
        while node is not None:
            if id(node) in seen or len(result) > 10000:
                raise ValueError('invalid list')
            seen.add(id(node)); d = dict(fields(node))
            if set(d) != {'val', 'next'}:
                raise TypeError('invalid list node')
            result.append(encode(d['val'], active)); node = d['next']
        return {'__list_node__': result}
    result = []; queue = [value]; seen = set()
    for node in queue:
        if node is None:
            result.append(None); continue
        if id(node) in seen or len(queue) > 20000:
            raise ValueError('invalid tree')
        seen.add(id(node)); d = dict(fields(node))
        if set(d) != {'val', 'left', 'right'}:
            raise TypeError('invalid tree node')
        result.append(encode(d['val'], active)); queue.extend((d['left'], d['right']))
    while result and result[-1] is None:
        result.pop()
    return {'__tree_node__': result}

def aliases(args, result):
    seen = {}; edges = []
    def walk(value, path):
        if value is None or type(value) in (str, bool, int, float):
            return
        if id(value) in seen:
            edges.append([path, seen[id(value)]]); return
        seen[id(value)] = path
        for key, item in fields(value):
            walk(item, path+'.'+str(key))
    walk(args, 'args'); walk(result, 'result')
    return edges

def main():
    packet = json.load(open('inputs.json'))
    namespace = {'__name__': 'candidate'}
    exec(compile(open('program.py').read(), 'program.py', 'exec'), namespace)
    for index, call in enumerate(packet['calls']):
        try:
            args = decode(call['args']); before = encode(args)
            result = namespace['solve'](*args)
            record = {'i': index, 'result': encode(result), 'result_type': type(result).__name__,
                      'args_before': before, 'args_after': encode(args), 'alias_edges': aliases(args, result)}
        except Exception as error:
            record = {'i': index, 'error': type(error).__name__+': '+str(error)[:300]}
        print(json.dumps(record, allow_nan=False, separators=(',', ':')))
    print(json.dumps({'done': len(packet['calls'])}))

if __name__ == '__main__':
    main()
