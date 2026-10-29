"""Direct native-class transport for the existing isolated judge; no expectations. Interfaces are INFERRED."""
import importlib.util
import json

# uid -> (class name, {method: arity}, void methods)
LAYOUT = {
    'hack2hire:68504f81839fbdf76404b1d1': ('SnapshotSet', {'add': 1, 'remove': 1, 'contains': 1, 'getIterator': 0, 'hasNext': 1, 'next': 1}, set()),
    'hack2hire:69dd8c3595e80ae213e5b9c7': ('ToDoList', {'add': 3, 'get': 1, 'updateStatus': 2, 'addDependency': 2, 'getDependencies': 1}, {'add'}),
    'hack2hire:69dd8d2795e80ae213e5b9cf': ('ToDoList', {'add': 3, 'get': 1, 'updateStatus': 2, 'addDependency': 2, 'getDependencies': 1, 'getExecutionOrder': 0}, {'add'}),
    'hack2hire:677b491778175fce2ecdfc10': ('FunctionLibrary', {'register': 3, 'findMatches': 1}, {'register'}),
}


def shape(uid, args):
    if type(uid) is not str or uid not in LAYOUT or type(args) is not list or len(args) != 2:
        raise ValueError('exact native identity and trace shape required')
    name, methods, _ = LAYOUT[uid]
    operations, rows = args
    if (type(operations) is not list or type(rows) is not list or not operations or
            len(operations) != len(rows) or type(operations[0]) is not str or operations[0] != name or
            type(rows[0]) is not list or rows[0] != []):
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
    receiver = native_class()
    if type(receiver) is not native_class:
        raise TypeError('native constructor must produce its own instance')
    outputs, snapshots, types = [None], [None], ['constructed']
    for operation, row in zip(args[0][1:], args[1][1:]):
        method = getattr(native_class, operation)
        value = method(receiver, *row)
        types.append(type(value).__name__)
        if operation in LAYOUT[uid][2] and value is not None:
            raise TypeError('void method returned a value')
        snapshots.append(transport.encode(value))
        outputs.append(value)
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
