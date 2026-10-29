"""Direct native-class transport for the existing isolated judge; no expectations (hack2hire-chunk10-b, INFERRED interfaces)."""
import importlib.util
import json

# uid -> (class name, constructor arity, {method: arity}, void methods)
LAYOUT = {
    'hack2hire:695d85f19c1c1f40daea73a0': ('TokenLimiter', 0, {'setPolicy': 5, 'consume': 3, 'getTokens': 2}, {'setPolicy'}),
    'hack2hire:68a4bbecc11d63d6052ea307': ('WorkerManagementSystem', 0, {'addWorker': 3, 'registerWorker': 2, 'get': 1}, set()),
    'hack2hire:68a4bbf8c11d63d6052ea308': ('WorkerManagementSystem', 0, {'addWorker': 3, 'registerWorker': 2, 'get': 1, 'topNWorkers': 2}, set()),
    'hack2hire:68a4bbfac11d63d6052ea309': ('WorkerManagementSystem', 0, {'addWorker': 3, 'registerWorker': 2, 'get': 1, 'topNWorkers': 2, 'promote': 4, 'calcSalary': 3}, set()),
    'hack2hire:68a4bbfbc11d63d6052ea30a': ('WorkerManagementSystem', 0, {'addWorker': 3, 'registerWorker': 2, 'get': 1, 'topNWorkers': 2, 'promote': 4, 'calcSalary': 3, 'setDoublePaid': 2}, {'setDoublePaid'}),
    'hack2hire:69efc8ea96981f58ae1f6d74': ('TaskManager', 0, {'addTask': 3, 'updateTask': 4, 'getTask': 2}, set()),
    'hack2hire:69efc92d96981f58ae1f6d75': ('TaskManager', 0, {'addTask': 3, 'updateTask': 4, 'getTask': 2, 'searchTasks': 3, 'listTasksSorted': 2}, set()),
    'hack2hire:69efc94196981f58ae1f6d76': ('TaskManager', 0, {'addTask': 3, 'updateTask': 4, 'getTask': 2, 'searchTasks': 3, 'listTasksSorted': 2, 'addUser': 3, 'assignTask': 4, 'getUserTasks': 2}, set()),
    'hack2hire:69efc96396981f58ae1f6d77': ('TaskManager', 0, {'addTask': 3, 'updateTask': 4, 'getTask': 2, 'searchTasks': 3, 'listTasksSorted': 2, 'addUser': 3, 'assignTask': 4, 'getUserTasks': 2, 'completeTask': 3, 'getOverdueAssignments': 2}, set()),
    'hack2hire:69026c73d18315042523a913': ('Paginator', 3, {'next': 0, 'prev': 0, 'goTo': 1}, set()),
    'hack2hire:685637ce4d16ce2ead6e1769': ('Codec', 0, {'encode': 1, 'decode': 1}, set()),
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
