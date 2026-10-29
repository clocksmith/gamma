"""Direct native-class transport for the existing isolated judge; no expectations (hack2hire-chunk10-a, INFERRED interfaces)."""
import importlib.util
import json

# uid -> (class name, constructor arity, {method: arity}, void methods)
LAYOUT = {
    'hack2hire:69d3f7fd79bf03c0074bce16': ('TemporalKVStore', 0, {'set': 3, 'get': 2, 'remove': 1}, {'set'}),
    'hack2hire:69dd59d595e80ae213e5b7fc': ('TemporalKVStore', 0, {'set': 3, 'get': 2, 'remove': 2}, {'set'}),
    'hack2hire:688d0850b6c09ad9a4fcc2db': ('RankedCache', 1, {'put': 3, 'get': 1}, {'put'}),
    'hack2hire:68aba144fc2e86fe2162e8a1': ('RankedCache', 2, {'put': 3, 'get': 1, 'getLoadCount': 0}, {'put'}),
    'hack2hire:69190b156723130c5456345c': ('ChatApp', 0, {'addBot': 2, 'sendMessage': 2, 'getRecentMessages': 1}, {'sendMessage'}),
    'hack2hire:691b8695419c66014d71411a': ('ChatApp', 0, {'createChannel': 1, 'addBot': 3, 'sendMessage': 3, 'getRecentMessages': 2}, set()),
    'hack2hire:677ed3ec052a260e0165706f': ('DelayedTaskScheduler', 0, {'schedule': 3, 'runDue': 1, 'cancel': 1}, set()),
    'hack2hire:691cfb5cba2fba0a9e173e8c': ('SQLManager', 0, {'createTable': 2, 'insert': 2, 'select': 4}, {'createTable'}),
    'hack2hire:6920d01494b324049c3251bd': ('KeyValueStore', 0, {'set': 2, 'get': 1, 'unset': 1}, {'set', 'unset'}),
    'hack2hire:6920d07794b324049c3251be': ('KeyValueStore', 0, {'set': 2, 'get': 1, 'unset': 1, 'begin': 0, 'rollback': 0, 'commit': 0}, {'set', 'unset', 'begin'}),
    'hack2hire:6920d4a994b324049c3251c1': ('KeyValueStore', 0, {'set': 2, 'get': 1, 'unset': 1, 'begin': 0, 'rollback': 0, 'commit': 0, 'count': 1}, {'set', 'unset', 'begin'}),
    'hack2hire:69b35205a4e93c007df404fe': ('SecondBrainSystem', 0, {'createNote': 3, 'getNote': 1, 'updateNote': 4, 'deleteNote': 1}, set()),
    'hack2hire:69b38216a4e93c007df405de': ('SecondBrainSystem', 0, {'createNote': 3, 'getNote': 1, 'updateNote': 4, 'deleteNote': 1, 'searchNotes': 1}, set()),
    'hack2hire:69b38409a4e93c007df405e6': ('SecondBrainSystem', 0, {'createNote': 3, 'getNote': 1, 'updateNote': 4, 'deleteNote': 1, 'searchNotes': 1, 'addTag': 2, 'removeTag': 2, 'getNotesByTag': 1}, set()),
    'hack2hire:69b385d3a4e93c007df405f1': ('SecondBrainSystem', 0, {'createNote': 3, 'getNote': 1, 'updateNote': 4, 'deleteNote': 1, 'searchNotes': 1, 'addTag': 2, 'removeTag': 2, 'getNotesByTag': 1, 'getVersionCount': 1, 'revertNote': 3}, set()),
    'hack2hire:691523d03f8671d8f7a56571': ('PersistentKVStore', 0, {'set': 2, 'get': 1, 'delete': 1, 'save': 0, 'load': 1}, {'set', 'load'}),
    'hack2hire:691523d43f8671d8f7a56572': ('PersistentKVStore', 0, {'set': 2, 'get': 1, 'delete': 1, 'save': 0, 'load': 1}, {'set'}),
    'hack2hire:67ce4e968f73eb6319edd1f0': ('RateLimiter', 2, {'allowRequest': 1}, set()),
    'hack2hire:67e0bdefa59c3d249d3625fe': ('RateLimiter', 2, {'allowRequest': 2}, set()),
    'hack2hire:67d44fdf488516fd8ad5a0ba': ('FileStorageSystem', 0, {'storeFile': 2, 'getKthRecentFiles': 1, 'returnAllFiles': 0}, {'storeFile'}),
    'hack2hire:69f2665342791c82ab992694': ('RecipeManager', 0, {'addRecipe': 3, 'getRecipe': 1, 'updateRecipe': 4, 'deleteRecipe': 1}, set()),
    'hack2hire:69f266df42791c82ab992697': ('RecipeManager', 0, {'addRecipe': 3, 'getRecipe': 1, 'updateRecipe': 4, 'deleteRecipe': 1, 'searchByIngredient': 1}, set()),
    'hack2hire:69f2674342791c82ab99269a': ('RecipeManager', 0, {'addRecipe': 3, 'getRecipe': 1, 'updateRecipe': 4, 'deleteRecipe': 1, 'searchByIngredient': 1, 'rateRecipe': 2, 'getTopRated': 1}, set()),
    'hack2hire:69f2676842791c82ab99269b': ('RecipeManager', 0, {'addRecipe': 3, 'getRecipe': 1, 'updateRecipe': 4, 'deleteRecipe': 1, 'searchByIngredient': 1, 'rateRecipe': 2, 'getTopRated': 1, 'listByNamePrefix': 1}, set()),
    'hack2hire:69d16c6917b72775cc49bf96': ('RingBuffer', 1, {'write': 1, 'read': 1}, {'write'}),
    'hack2hire:696bebd76b040fa4d120bb7a': ('SquirrelResearch', 0, {'hideNuts': 2, 'retrieveNuts': 2, 'getHighestLevel': 1}, set()),
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
