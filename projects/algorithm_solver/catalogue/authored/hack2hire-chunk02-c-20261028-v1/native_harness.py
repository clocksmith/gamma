"""Direct native-class transport for the existing isolated judge; no expectations. Identities are hack2hire uid strings."""
import importlib.util
import json

# uid -> (class name, constructor arity, {method: arity}, void methods normalised to null)
LAYOUT = {
    'hack2hire:6778936c775a4a31045ead0e': ('WindowedKeyValueStore', 2, {'put': 3, 'get': 2}, {'put'}),
    'hack2hire:67957d70010c9ed2f849b1f9': ('TransactionSystem', 2, {'getBalance': 1, 'getBalances': 0}, set()),
    'hack2hire:67957d75010c9ed2f849b1fa': ('TransactionSystem', 2, {'getBalance': 1, 'getBalances': 0, 'getBalanceAfter': 2}, set()),
    'hack2hire:6a121534653f4ff494e2c7ea': ('CameraLogServer', 0, {'requestLog': 2, 'pollCommand': 1, 'sendLog': 3, 'pollLog': 0}, {'requestLog', 'sendLog'}),
    'hack2hire:689cf810aee746eb1c84ba38': ('CloudStorage', 0, {'addFile': 2, 'copyFile': 2, 'getFilesize': 1}, set()),
    'hack2hire:689e4cd5735253d430dee92d': ('CloudStorage', 0, {'addFile': 2, 'copyFile': 2, 'getFilesize': 1, 'findFile': 2}, set()),
    'hack2hire:689e4cd8735253d430dee92e': ('CloudStorage', 0, {'addFile': 2, 'copyFile': 2, 'getFilesize': 1, 'findFile': 2, 'addUser': 2, 'addFileBy': 3, 'mergeUser': 2}, set()),
    'hack2hire:689e4cd9735253d430dee92f': ('CloudStorage', 0, {'addFile': 2, 'copyFile': 2, 'getFilesize': 1, 'findFile': 2, 'addUser': 2, 'addFileBy': 3, 'mergeUser': 2, 'backupUser': 1, 'restoreUser': 1}, set()),
    'hack2hire:6855e42cc201117d348a2630': ('CustomerRevenueSystem', 0, {'insert': 1, 'insertWithReferrer': 2, 'getLowestK': 2}, set()),
    'hack2hire:69445eb8867a3f9f539ff53d': ('CustomerRevenueSystem', 0, {'insert': 1, 'insertWithReferrer': 2, 'getLowestK': 2, 'getNestedRevenue': 2}, set()),
    'hack2hire:68b93d5483188776facc8ff6': ('ConnectFour', 0, {'play': 1}, set()),
    'hack2hire:67a19e53b41c4108d8ccb3d4': ('InMemoryKVDB', 0, {'set': 2, 'get': 1, 'delete': 1, 'count': 1, 'begin': 0, 'rollback': 0, 'commit': 0}, {'begin', 'delete', 'set'}),
    'hack2hire:677ae48578175fce2ecdfc0a': ('DocumentLibrary', 1, {'search': 1}, set()),
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
    if (type(packet) is not dict or set(packet) != {'schema', 'native_problem_uid', 'calls'} or
            packet['schema'] != 'gamma.native-class-transport.v1' or type(packet['calls']) is not list or
            type(packet['native_problem_uid']) is not str or packet['native_problem_uid'] not in LAYOUT):
        raise ValueError('fixed argument-only native packet required')
    spec = importlib.util.spec_from_file_location('native_transport', 'transport.py')
    transport = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(transport)
    namespace = {'__name__': 'candidate'}
    with open('program.py') as stream: raw = stream.read()
    exec(compile(raw, 'program.py', 'exec'), namespace)
    for index, call in enumerate(packet['calls']):
        try:
            record = {'i': index, **observe(namespace, packet['native_problem_uid'], call, transport)}
        except Exception as error:
            record = {'i': index, 'error': type(error).__name__ + ': ' + str(error)[:300]}
        print(json.dumps(record, allow_nan=False, separators=(',', ':')))
    print(json.dumps({'done': len(packet['calls'])}))


if __name__ == '__main__': main()
