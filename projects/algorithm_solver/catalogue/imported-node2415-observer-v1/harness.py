"""Native2415 transport successor. No expected answers or value permutation.

Only a singleton perfect tree is admitted. Original classes, class descriptors,
own data-field layout, pointers and root identity must survive the call. Values
are merely observed; their allowed permutation is checked outside the sandbox.
The historical observer and all executor resource caps remain unchanged.
"""
import json


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val, self.left, self.right = val, left, right


def decode_args(args):
    if type(args) is not list or len(args) != 1 or type(args[0]) is not dict or set(args[0]) != {'__tree_node__'}:
        raise ValueError('native2415 requires one tree argument')
    values = args[0]['__tree_node__']
    if (type(values) is not list or not 1 <= len(values) <= 16383 or
            (len(values) + 1) & len(values) or
            any(type(v) is not int or not 0 <= v <= 100000 for v in values)):
        raise ValueError('native2415 requires bounded perfect integer tree')
    nodes = [TreeNode(v) for v in values]
    for i, node in enumerate(nodes):
        if 2*i+1 < len(nodes): node.left, node.right = nodes[2*i+1], nodes[2*i+2]
    return [nodes[0]]


def capture_nodes(args):
    """Capture physical identity before loading/calling the candidate.

    Python instances have own dictionary data fields rather than JS property
    flags. Preserve that exact field set and the original class/MRO descriptors;
    a property, slot, subclass or __getattribute__ replacement is not equivalent.
    """
    if type(args) is not list or len(args) != 1 or type(args[0]) is not TreeNode:
        raise TypeError('native2415 original TreeNode required')
    node_type = TreeNode
    get_data = object.__getattribute__
    class_chain = tuple((cls, dict(vars(cls))) for cls in node_type.__mro__)
    original_mro = node_type.__mro__
    # These type-managed attributes need not appear in vars(TreeNode).
    class_metadata = (type(node_type), node_type.__name__, node_type.__qualname__, node_type.__bases__)
    nodes, links, before, seen = [args[0]], [], [], set()
    for node in nodes:
        if len(nodes) > 200000 or len(nodes) > 16383 or type(node) is not node_type or id(node) in seen:
            raise ValueError('invalid original tree identity')
        seen.add(id(node))
        data = get_data(node, '__dict__')
        if type(data) is not dict or set(data) != {'val', 'left', 'right'}:
            raise TypeError('invalid original own fields')
        if type(data['val']) is not int or not 0 <= data['val'] <= 100000:
            raise ValueError('invalid node value')
        children = (data['left'], data['right'])
        links.append(children)
        state = {'value': data['val'], 'left': None, 'right': None}
        for key, child in zip(('left', 'right'), children):
            if child is not None:
                state[key] = len(nodes); nodes.append(child)
        before.append(state)
    n = len(nodes)
    # This is the representation bound, not a larger sandbox/identity budget.
    # At most n real nodes and 2*n+1 BFS slots (32767 at the domain maximum).
    if (n + 1) & n: raise ValueError('perfect tree required')
    for i, state in enumerate(before):
        if state['left'] != (2*i+1 if 2*i+1 < n else None) or state['right'] != (2*i+2 if 2*i+2 < n else None):
            raise ValueError('perfect tree required')

    def finish(result):
        if result is not nodes[0] or args[0] is not nodes[0]:
            raise ValueError('original root identity changed')
        if (type(node_type), node_type.__name__, node_type.__qualname__, node_type.__bases__) != class_metadata:
            raise TypeError('original class metadata changed')
        if node_type.__mro__ != original_mro:
            raise TypeError('original class hierarchy changed')
        for cls, descriptors in class_chain:
            current = vars(cls)
            if set(current) != set(descriptors) or any(current[key] is not value for key, value in descriptors.items()):
                raise TypeError('original class descriptors changed')
        after = []
        for i, node in enumerate(nodes):
            if type(node) is not node_type:
                raise TypeError('original node class changed')
            data = get_data(node, '__dict__')
            if type(data) is not dict or set(data) != {'val', 'left', 'right'}:
                raise TypeError('original own fields changed')
            if type(data['val']) is not int or not 0 <= data['val'] <= 100000:
                raise ValueError('invalid node value')
            if data['left'] is not links[i][0] or data['right'] is not links[i][1]:
                raise ValueError('original node links changed')
            after.append({'value': data['val'], 'left': before[i]['left'], 'right': before[i]['right']})
        # Only after every physical check succeeds may an observation be emitted.
        # The verified tree has no internal aliases; identical argument/result
        # root references yield precisely this single observed cross-root edge.
        return {'result': {'__tree_node__': [state['value'] for state in after]},
                'result_type': node_type.__name__,
                'args_before': [{'__tree_node__': [state['value'] for state in before]}],
                'args_after': [{'__tree_node__': [state['value'] for state in after]}],
                'alias_edges': [['result', 'args.0']],
                'node_identity': {'before': before, 'after': after, 'argument_roots': [0], 'result_root': 0},
                'node_integrity': {'schema': 'gamma.native2415-node-integrity.v1', 'node_count': n,
                                   'class_or_prototype_unchanged': True, 'own_field_descriptors_unchanged': True}}
    return finish


def main():
    with open('inputs.json') as stream: packet = json.load(stream)
    if (packet.get('entry') != 'solve' or packet.get('method') != 'solve' or packet.get('node_identity') is not True or
            type(packet.get('calls')) is not list or len(packet['calls']) != 1 or
            type(packet['calls'][0]) is not dict or set(packet['calls'][0]) != {'args'}):
        raise ValueError('native2415 requires singleton solve packet')
    try:
        args = decode_args(packet['calls'][0]['args']); finish = capture_nodes(args)
        namespace = {'__name__': 'candidate'}
        with open('program.py') as stream: source = stream.read()
        exec(compile(source, 'program.py', 'exec'), namespace)
        record = {'i': 0, **finish(namespace['solve'](*args))}
    except Exception as error:
        record = {'i': 0, 'error': type(error).__name__ + ': ' + str(error)[:300]}
    print(json.dumps(record, allow_nan=False, separators=(',', ':')))
    print(json.dumps({'done': 1}))


if __name__ == '__main__': main()
