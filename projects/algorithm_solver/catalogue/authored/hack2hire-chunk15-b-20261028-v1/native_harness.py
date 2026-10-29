"""Direct native-class transport for the existing isolated judge; no expectations (hack2hire-chunk15-b, INFERRED interfaces)."""
import importlib.util
import json

# uid -> (class name, constructor arity, {method: arity}, void methods)
LAYOUT = {
    'hack2hire:689505e73a1d9e6d6042d51a': ('InMemoryDB', 0, {'setData': 3, 'getData': 2, 'deleteData': 2}, {'setData'}),
    'hack2hire:68961c873a1d9e6d6042d57a': ('InMemoryDB', 0, {'setData': 3, 'getData': 2, 'deleteData': 2, 'scanData': 1, 'scanDataByPrefix': 2}, {'setData'}),
    'hack2hire:689641c83a1d9e6d6042d585': ('InMemoryDB', 0, {'setDataAt': 4, 'setDataAtWithTtl': 5, 'deleteDataAt': 3, 'getDataAt': 3, 'scanDataAt': 2, 'scanDataByPrefixAt': 3}, {'setDataAt', 'setDataAtWithTtl'}),
    'hack2hire:689bb2061126a03aace65e39': ('InMemoryDB', 0, {'setDataAt': 4, 'setDataAtWithTtl': 5, 'deleteDataAt': 3, 'getDataAt': 3, 'scanDataAt': 2, 'scanDataByPrefixAt': 3, 'backup': 1, 'restore': 2}, {'setDataAt', 'setDataAtWithTtl', 'restore'}),
    'hack2hire:677df76b052a260e0165706c': ('InfiniteQueue', 0, {'add': 1, 'poll': 0, 'getRandom': 1}, {'add'}),
    'hack2hire:68539b6bd3dbd4fb8b026e9f': ('LazyArray', 1, {'map': 2, 'indexOf': 1}, {'map'}),
    'hack2hire:681bc967a73bd75b806cb994': ('EscapeRoom', 2, {'advance': 1, 'countInRoom': 1, 'topPlayers': 1}, {'advance'}),
    'hack2hire:68edc9c15abdefad4f6693fc': ('EventLogger', 1, {'logEvent': 2}, set()),
}


def shape(uid, args):
    if type(uid) is not str or uid not in LAYOUT or type(args) is not list or len(args) != 2:
        raise ValueError('exact native identity and trace shape required')
    name, ctor, methods, _ = LAYOUT[uid]
    operations, rows = args
    if (type(operations) is not list or type(rows) is not list or not operations or
            len(operations) != len(rows) or type(operations[0]) is not str or operations[0] != name or
            type(rows[0]) is not list or len(rows[0]) != ctor):
        raise ValueError('exact one initial constructor required')
    for operation, row in zip(operations[1:], rows[1:]):
        if type(operation) is not str or operation not in methods or type(row) is not list or len(row) != methods[operation]:
            raise ValueError('unapproved native method or arity')
    return name, methods


def observe(namespace, uid, call, transport):
    if type(call) is not dict or set(call) != {'args'}:
        raise ValueError('argument-only call required')
    args = transport.decode(call['args'])
    name, _ = shape(uid, args)
    native_class = namespace.get(name)
    if type(native_class) is not type:
        raise TypeError('original named class required; no solve fallback or injected constructor')
    before = transport.encode(args)
    receiver = native_class(*args[1][0])
    if type(receiver) is not native_class:
        raise TypeError('native constructor must produce its own instance')
    outputs, snapshots, types = [None], [None], ['constructed']
    for operation, row in zip(args[0][1:], args[1][1:]):
        # Use the original class's method with the same receiver every time.
        method = getattr(native_class, operation)
        value = method(receiver, *row)
        types.append(type(value).__name__)
        normalized = None if operation in LAYOUT[uid][3] else value
        snapshots.append(transport.encode(normalized))
        outputs.append(normalized)
    return {'result': transport.encode(outputs), 'result_type': type(outputs).__name__,
            'args_before': before, 'args_after': transport.encode(args),
            'alias_edges': transport.aliases(args, outputs),
            'native_route': 'direct-class-v1', 'native_class': name, 'native_receiver_count': 1,
            'native_method_return_types': types, 'native_method_snapshots': snapshots}


def main():
    with open('inputs.json') as stream: packet = json.load(stream)
    if (type(packet) is not dict or set(packet) != {'schema', 'native_problem_id', 'calls'} or
            packet['schema'] != 'gamma.native-class-transport.v1' or type(packet['calls']) is not list or
            type(packet['native_problem_id']) is not str or packet['native_problem_id'] not in LAYOUT):
        raise ValueError('fixed argument-only native packet required')
    spec = importlib.util.spec_from_file_location('native_transport', 'transport.py')
    transport = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(transport)
    namespace = {'__name__': 'candidate'}
    with open('program.py') as stream: raw = stream.read()
    exec(compile(raw, 'program.py', 'exec'), namespace)
    for index, call in enumerate(packet['calls']):
        try:
            record = {'i': index, **observe(namespace, packet['native_problem_id'], call, transport)}
        except Exception as error:
            record = {'i': index, 'error': type(error).__name__ + ': ' + str(error)[:300]}
        print(json.dumps(record, allow_nan=False, separators=(',', ':')))
    print(json.dumps({'done': len(packet['calls'])}))


if __name__ == '__main__': main()
