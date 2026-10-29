"""Direct native-class transport for the existing isolated judge; no expectations. Identities are hack2hire uid strings."""
import importlib.util
import json

# uid -> (class name, constructor arity, {method: arity}, void methods normalised to null)
LAYOUT = {
    'hack2hire:687c3a5eaa2b26b0b64b39e5': ('BankingSystem', 0, {'createAccount': 2, 'deposit': 3, 'transfer': 4}, set()),
    'hack2hire:687c4741aa2b26b0b64b39ee': ('BankingSystem', 0, {'createAccount': 2, 'deposit': 3, 'transfer': 4, 'topSpenders': 2}, set()),
    'hack2hire:687c4e56024483ac76db8c9b': ('BankingSystem', 0, {'createAccount': 2, 'deposit': 3, 'transfer': 4, 'topSpenders': 2, 'pay': 3, 'getPaymentStatus': 3}, set()),
    'hack2hire:687c5c0b024483ac76db8ca2': ('BankingSystem', 0, {'createAccount': 2, 'deposit': 3, 'transfer': 4, 'topSpenders': 2, 'pay': 3, 'getPaymentStatus': 3, 'mergeAccounts': 3, 'getBalance': 3}, set()),
    'hack2hire:69178d9a10632c00111ca20d': ('DeliverySystem', 0, {'addDriver': 2, 'addDelivery': 3, 'getTotalCost': 0}, {'addDelivery', 'addDriver'}),
    'hack2hire:6917944e10632c00111ca217': ('DeliverySystem', 0, {'addDriver': 2, 'addDelivery': 3, 'getTotalCost': 0, 'payUpTo': 1, 'getTotalCostUnpaid': 0}, {'addDelivery', 'addDriver', 'payUpTo'}),
    'hack2hire:6917944f10632c00111ca218': ('DeliverySystem', 0, {'addDriver': 2, 'addDelivery': 3, 'getTotalCost': 0, 'payUpTo': 1, 'getTotalCostUnpaid': 0, 'getMaxActiveDriversInLast24Hours': 1}, {'addDelivery', 'addDriver', 'payUpTo'}),
    'hack2hire:69c19a8521f6ab4226964bf7': ('ConnectKGame', 1, {'placePiece': 2}, set()),
    'hack2hire:69d16c5617b72775cc49bf93': ('Document', 0, {'setProperty': 3, 'getProperty': 2, 'undo': 0}, {'setProperty'}),
    'hack2hire:69d1730e17b72775cc49bfc6': ('Document', 0, {'setProperty': 3, 'getProperty': 2, 'undo': 0, 'redo': 0}, {'setProperty'}),
    'hack2hire:69d1735f17b72775cc49bfc7': ('Document', 0, {'setProperty': 3, 'getProperty': 2, 'undo': 0, 'redo': 0, 'removeProperty': 2, 'getProperties': 1}, {'setProperty'}),
    'hack2hire:6941be52b9d646bec48c68cc': ('TennisGame', 0, {'pointTo': 1, 'getPoints': 0, 'getScore': 0, 'getWinner': 0}, {'pointTo'}),
    'hack2hire:6941c912e79fe20cf9ff4435': ('TennisSet', 0, {'pointTo': 1, 'getGames': 0, 'getGameScore': 0, 'getWinner': 0}, {'pointTo'}),
    'hack2hire:683e86418d3dfb7c9bd756ab': ('FileSystem', 0, {'addFile': 2, 'find': 2}, {'addFile'}),
    'hack2hire:683f1dc68d3dfb7c9bd756da': ('FileSystem', 0, {'addFile': 2, 'find': 2}, {'addFile'}),
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
