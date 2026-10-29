'use strict';
// Direct native-class transport for the existing isolated judge; no expectations (hack2hire-chunk10-a, INFERRED interfaces).
const fs = require('fs');
const APPLY = Reflect.apply, CONSTRUCT = Reflect.construct, PROTOTYPE = Object.getPrototypeOf;
// uid -> [class name, constructor arity, {method: arity}, void methods]
const LAYOUT = {
  "hack2hire:69d3f7fd79bf03c0074bce16": ["TemporalKVStore", 0, {set: 3, get: 2, remove: 1}, new Set(["set"])],
  "hack2hire:69dd59d595e80ae213e5b7fc": ["TemporalKVStore", 0, {set: 3, get: 2, remove: 2}, new Set(["set"])],
  "hack2hire:688d0850b6c09ad9a4fcc2db": ["RankedCache", 1, {put: 3, get: 1}, new Set(["put"])],
  "hack2hire:68aba144fc2e86fe2162e8a1": ["RankedCache", 2, {put: 3, get: 1, getLoadCount: 0}, new Set(["put"])],
  "hack2hire:69190b156723130c5456345c": ["ChatApp", 0, {addBot: 2, sendMessage: 2, getRecentMessages: 1}, new Set(["sendMessage"])],
  "hack2hire:691b8695419c66014d71411a": ["ChatApp", 0, {createChannel: 1, addBot: 3, sendMessage: 3, getRecentMessages: 2}, new Set([])],
  "hack2hire:677ed3ec052a260e0165706f": ["DelayedTaskScheduler", 0, {schedule: 3, runDue: 1, cancel: 1}, new Set([])],
  "hack2hire:691cfb5cba2fba0a9e173e8c": ["SQLManager", 0, {createTable: 2, insert: 2, select: 4}, new Set(["createTable"])],
  "hack2hire:6920d01494b324049c3251bd": ["KeyValueStore", 0, {set: 2, get: 1, unset: 1}, new Set(["set", "unset"])],
  "hack2hire:6920d07794b324049c3251be": ["KeyValueStore", 0, {set: 2, get: 1, unset: 1, begin: 0, rollback: 0, commit: 0}, new Set(["set", "unset", "begin"])],
  "hack2hire:6920d4a994b324049c3251c1": ["KeyValueStore", 0, {set: 2, get: 1, unset: 1, begin: 0, rollback: 0, commit: 0, count: 1}, new Set(["set", "unset", "begin"])],
  "hack2hire:69b35205a4e93c007df404fe": ["SecondBrainSystem", 0, {createNote: 3, getNote: 1, updateNote: 4, deleteNote: 1}, new Set([])],
  "hack2hire:69b38216a4e93c007df405de": ["SecondBrainSystem", 0, {createNote: 3, getNote: 1, updateNote: 4, deleteNote: 1, searchNotes: 1}, new Set([])],
  "hack2hire:69b38409a4e93c007df405e6": ["SecondBrainSystem", 0, {createNote: 3, getNote: 1, updateNote: 4, deleteNote: 1, searchNotes: 1, addTag: 2, removeTag: 2, getNotesByTag: 1}, new Set([])],
  "hack2hire:69b385d3a4e93c007df405f1": ["SecondBrainSystem", 0, {createNote: 3, getNote: 1, updateNote: 4, deleteNote: 1, searchNotes: 1, addTag: 2, removeTag: 2, getNotesByTag: 1, getVersionCount: 1, revertNote: 3}, new Set([])],
  "hack2hire:691523d03f8671d8f7a56571": ["PersistentKVStore", 0, {set: 2, get: 1, delete: 1, save: 0, load: 1}, new Set(["set", "load"])],
  "hack2hire:691523d43f8671d8f7a56572": ["PersistentKVStore", 0, {set: 2, get: 1, delete: 1, save: 0, load: 1}, new Set(["set"])],
  "hack2hire:67ce4e968f73eb6319edd1f0": ["RateLimiter", 2, {allowRequest: 1}, new Set([])],
  "hack2hire:67e0bdefa59c3d249d3625fe": ["RateLimiter", 2, {allowRequest: 2}, new Set([])],
  "hack2hire:67d44fdf488516fd8ad5a0ba": ["FileStorageSystem", 0, {storeFile: 2, getKthRecentFiles: 1, returnAllFiles: 0}, new Set(["storeFile"])],
  "hack2hire:69f2665342791c82ab992694": ["RecipeManager", 0, {addRecipe: 3, getRecipe: 1, updateRecipe: 4, deleteRecipe: 1}, new Set([])],
  "hack2hire:69f266df42791c82ab992697": ["RecipeManager", 0, {addRecipe: 3, getRecipe: 1, updateRecipe: 4, deleteRecipe: 1, searchByIngredient: 1}, new Set([])],
  "hack2hire:69f2674342791c82ab99269a": ["RecipeManager", 0, {addRecipe: 3, getRecipe: 1, updateRecipe: 4, deleteRecipe: 1, searchByIngredient: 1, rateRecipe: 2, getTopRated: 1}, new Set([])],
  "hack2hire:69f2676842791c82ab99269b": ["RecipeManager", 0, {addRecipe: 3, getRecipe: 1, updateRecipe: 4, deleteRecipe: 1, searchByIngredient: 1, rateRecipe: 2, getTopRated: 1, listByNamePrefix: 1}, new Set([])],
  "hack2hire:69d16c6917b72775cc49bf96": ["RingBuffer", 1, {write: 1, read: 1}, new Set(["write"])],
  "hack2hire:696bebd76b040fa4d120bb7a": ["SquirrelResearch", 0, {hideNuts: 2, retrieveNuts: 2, getHighestLevel: 1}, new Set([])],
};

function shape(uid, args) {
  if (typeof uid !== 'string' || !Object.hasOwn(LAYOUT, uid) || !Array.isArray(args) || args.length !== 2) throw Error('exact native identity and trace shape required');
  const [name, ctor, methods] = LAYOUT[uid], [operations, rows] = args;
  if (!Array.isArray(operations) || !Array.isArray(rows) || !operations.length || operations.length !== rows.length || operations[0] !== name || !Array.isArray(rows[0]) || rows[0].length !== ctor) throw Error('exact initial constructor required');
  for (let i = 1; i < operations.length; i++) {
    if (typeof operations[i] !== 'string' || !Object.hasOwn(methods, operations[i]) || !Array.isArray(rows[i]) || rows[i].length !== methods[operations[i]]) throw Error('unapproved native method or arity');
  }
  return [name, methods];
}

function observe(exported, uid, call, transport) {
  if (call === null || typeof call !== 'object' || Array.isArray(call) || Object.keys(call).length !== 1 || !Object.hasOwn(call, 'args')) throw Error('argument-only call required');
  const args = transport.decode(call.args), [name] = shape(uid, args);
  const NativeClass = exported && exported[name];
  if (typeof NativeClass !== 'function') throw Error('original named class export required; no solve fallback or injected constructor');
  const before = transport.encode(args), receiver = CONSTRUCT(NativeClass, args[1][0]);
  if (PROTOTYPE(receiver) !== NativeClass.prototype) throw Error('native constructor must produce its own instance');
  const outputs = [null], snapshots = [null], types = ['constructed'];
  for (let i = 1; i < args[0].length; i++) {
    const operation = args[0][i], method = NativeClass.prototype[operation];
    if (typeof method !== 'function') throw Error('declared native prototype method missing');
    const value = APPLY(method, receiver, args[1][i]);
    types.push(typeof value);
    const normalized = LAYOUT[uid][3].has(operation) ? null : value;
    snapshots.push(transport.encode(normalized));
    outputs.push(normalized);
  }
  return {result: transport.encode(outputs), result_type: typeof outputs,
    args_before: before, args_after: transport.encode(args), alias_edges: transport.aliases(args, outputs),
    native_route: 'direct-class-v1', native_class: name, native_receiver_count: 1,
    native_method_return_types: types, native_method_snapshots: snapshots};
}

function main() {
  const packet = JSON.parse(fs.readFileSync('inputs.json', 'utf8'));
  if (packet === null || typeof packet !== 'object' || Array.isArray(packet) || Object.keys(packet).sort().join(',') !== 'calls,native_problem_id,schema' || packet.schema !== 'gamma.native-class-transport.v1' || typeof packet.native_problem_id !== 'string' || !Object.hasOwn(LAYOUT, packet.native_problem_id) || !Array.isArray(packet.calls)) throw Error('fixed argument-only native packet required');
  const transport = require('./transport.cjs');
  const exported = require('./program.cjs');
  for (let i = 0; i < packet.calls.length; i++) {
    let record;
    try { record = {i, ...observe(exported, packet.native_problem_id, packet.calls[i], transport)}; }
    catch (error) { record = {i, error: String(error).slice(0, 300)}; }
    process.stdout.write(JSON.stringify(record) + '\n');
  }
  process.stdout.write(JSON.stringify({done: packet.calls.length}) + '\n');
}

if (require.main === module) main();
module.exports = {LAYOUT, shape, observe};
