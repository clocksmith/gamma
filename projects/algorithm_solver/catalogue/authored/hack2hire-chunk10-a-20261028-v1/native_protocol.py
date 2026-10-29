"""Host-only bridge to the existing judge's direct-class observation records (hack2hire-chunk10-a, INFERRED interfaces)."""
import importlib.util
import json
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('gamma_h2h10a_native_host_oracles', Path(__file__).with_name('oracles.py'))
oracle = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(oracle)
# inferred return type per method -> (python type name, javascript typeof)
KIND = {'boolean': ('bool', 'boolean'), 'integer': ('int', 'number'), 'string': ('str', 'string'), 'string[]': ('list', 'object'),
        'integer[]': ('list', 'object'), 'string[][]': ('list', 'object'), 'list<[string,string,integer,integer]>': ('list', 'object'),
        'list<[string,string[],string[]]>': ('list', 'object'), 'void': ('NoneType', 'undefined')}
RETURNS = {
 "hack2hire:69d3f7fd79bf03c0074bce16": {
  "set": "void",
  "get": "string",
  "remove": "boolean"
 },
 "hack2hire:69dd59d595e80ae213e5b7fc": {
  "set": "void",
  "get": "string",
  "remove": "boolean"
 },
 "hack2hire:688d0850b6c09ad9a4fcc2db": {
  "put": "void",
  "get": "string"
 },
 "hack2hire:68aba144fc2e86fe2162e8a1": {
  "put": "void",
  "get": "string",
  "getLoadCount": "integer"
 },
 "hack2hire:69190b156723130c5456345c": {
  "addBot": "boolean",
  "sendMessage": "void",
  "getRecentMessages": "string[]"
 },
 "hack2hire:691b8695419c66014d71411a": {
  "createChannel": "boolean",
  "addBot": "boolean",
  "sendMessage": "boolean",
  "getRecentMessages": "string[]"
 },
 "hack2hire:677ed3ec052a260e0165706f": {
  "schedule": "integer",
  "runDue": "string[]",
  "cancel": "boolean"
 },
 "hack2hire:691cfb5cba2fba0a9e173e8c": {
  "createTable": "void",
  "insert": "boolean",
  "select": "string[][]"
 },
 "hack2hire:6920d01494b324049c3251bd": {
  "set": "void",
  "get": "string",
  "unset": "void"
 },
 "hack2hire:6920d07794b324049c3251be": {
  "set": "void",
  "get": "string",
  "unset": "void",
  "begin": "void",
  "rollback": "boolean",
  "commit": "boolean"
 },
 "hack2hire:6920d4a994b324049c3251c1": {
  "set": "void",
  "get": "string",
  "unset": "void",
  "begin": "void",
  "rollback": "boolean",
  "commit": "boolean",
  "count": "integer"
 },
 "hack2hire:69b35205a4e93c007df404fe": {
  "createNote": "string",
  "getNote": "list<[string,string,integer,integer]>",
  "updateNote": "boolean",
  "deleteNote": "boolean"
 },
 "hack2hire:69b38216a4e93c007df405de": {
  "createNote": "string",
  "getNote": "list<[string,string,integer,integer]>",
  "updateNote": "boolean",
  "deleteNote": "boolean",
  "searchNotes": "string[]"
 },
 "hack2hire:69b38409a4e93c007df405e6": {
  "createNote": "string",
  "getNote": "list<[string,string,integer,integer]>",
  "updateNote": "boolean",
  "deleteNote": "boolean",
  "searchNotes": "string[]",
  "addTag": "boolean",
  "removeTag": "boolean",
  "getNotesByTag": "string[]"
 },
 "hack2hire:69b385d3a4e93c007df405f1": {
  "createNote": "string",
  "getNote": "list<[string,string,integer,integer]>",
  "updateNote": "boolean",
  "deleteNote": "boolean",
  "searchNotes": "string[]",
  "addTag": "boolean",
  "removeTag": "boolean",
  "getNotesByTag": "string[]",
  "getVersionCount": "integer",
  "revertNote": "boolean"
 },
 "hack2hire:691523d03f8671d8f7a56571": {
  "set": "void",
  "get": "string",
  "delete": "boolean",
  "save": "integer[]",
  "load": "void"
 },
 "hack2hire:691523d43f8671d8f7a56572": {
  "set": "void",
  "get": "string",
  "delete": "boolean",
  "save": "integer[]",
  "load": "boolean"
 },
 "hack2hire:67ce4e968f73eb6319edd1f0": {
  "allowRequest": "boolean"
 },
 "hack2hire:67e0bdefa59c3d249d3625fe": {
  "allowRequest": "boolean"
 },
 "hack2hire:67d44fdf488516fd8ad5a0ba": {
  "storeFile": "void",
  "getKthRecentFiles": "string[]",
  "returnAllFiles": "string[]"
 },
 "hack2hire:69f2665342791c82ab992694": {
  "addRecipe": "string",
  "getRecipe": "list<[string,string[],string[]]>",
  "updateRecipe": "boolean",
  "deleteRecipe": "boolean"
 },
 "hack2hire:69f266df42791c82ab992697": {
  "addRecipe": "string",
  "getRecipe": "list<[string,string[],string[]]>",
  "updateRecipe": "boolean",
  "deleteRecipe": "boolean",
  "searchByIngredient": "string[]"
 },
 "hack2hire:69f2674342791c82ab99269a": {
  "addRecipe": "string",
  "getRecipe": "list<[string,string[],string[]]>",
  "updateRecipe": "boolean",
  "deleteRecipe": "boolean",
  "searchByIngredient": "string[]",
  "rateRecipe": "boolean",
  "getTopRated": "string[]"
 },
 "hack2hire:69f2676842791c82ab99269b": {
  "addRecipe": "string",
  "getRecipe": "list<[string,string[],string[]]>",
  "updateRecipe": "boolean",
  "deleteRecipe": "boolean",
  "searchByIngredient": "string[]",
  "rateRecipe": "boolean",
  "getTopRated": "string[]",
  "listByNamePrefix": "string[]"
 },
 "hack2hire:69d16c6917b72775cc49bf96": {
  "write": "void",
  "read": "string"
 },
 "hack2hire:696bebd76b040fa4d120bb7a": {
  "hideNuts": "integer",
  "retrieveNuts": "integer",
  "getHighestLevel": "integer"
 }
}


def exact(a, b):
    if type(a) is not type(b): return False
    if type(a) is list: return len(a) == len(b) and all(map(exact, a, b))
    if type(a) is dict: return a.keys() == b.keys() and all(exact(a[k], b[k]) for k in a)
    return a == b


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def packet(uid, cases, *, maximum_bytes):
    """Caller supplies its already approved packet cap; this grants no new cap."""
    if type(maximum_bytes) is not int or maximum_bytes <= 0:
        raise ValueError('existing positive exact packet bound required')
    if type(uid) is not str or uid not in oracle.CLASSES or type(cases) is not list or not cases:
        raise ValueError('assigned native identity and nonempty bounded case list required')
    calls = []
    for case in cases:
        if type(case) is not dict or 'args' not in case: raise ValueError('case arguments required')
        oracle.validate_domain(uid, case['args'])
        calls.append({'args': case['args']})
    raw = encoded({'schema': 'gamma.native-class-transport.v1', 'native_problem_id': uid, 'calls': calls})
    if len(raw) > maximum_bytes: raise ValueError('native packet exceeds existing caller bound')
    return raw


def check(uid, args, observed, expected, language):
    if language not in ('python', 'javascript'): raise ValueError('fixed language required')
    oracle.validate_domain(uid, args)
    if type(observed) is not dict or 'error' in observed: return 'candidate_error'
    if not exact(observed.get('result'), expected): return 'wrong_answer'
    if (not exact(observed.get('args_before'), args) or not exact(observed.get('args_after'), args) or
            not exact(observed.get('alias_edges'), [])):
        return 'effects'
    if (observed.get('native_route') != 'direct-class-v1' or observed.get('native_class') != oracle.CLASSES[uid][0] or
            type(observed.get('native_receiver_count')) is not int or observed['native_receiver_count'] != 1 or
            observed.get('result_type') != ('list' if language == 'python' else 'object') or
            not exact(observed.get('native_method_snapshots'), expected)):
        return 'native_interface'
    column = 0 if language == 'python' else 1
    kinds = ['constructed'] + [KIND[RETURNS[uid][op]][column] for op in args[0][1:]]
    if not exact(observed.get('native_method_return_types'), kinds):
        return 'native_return_type'
    return None
