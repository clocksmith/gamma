'use strict';
const fs = require('fs');
const APPLY = Reflect.apply, CONSTRUCT = Reflect.construct, PROTOTYPE = Object.getPrototypeOf;
// uid -> [class name, constructor arity, {method: arity}, void methods normalised to null]
const LAYOUT = {
  'hack2hire:6778936c775a4a31045ead0e': ['WindowedKeyValueStore', 2, {put: 3, get: 2}, new Set(["put"])],
  'hack2hire:67957d70010c9ed2f849b1f9': ['TransactionSystem', 2, {getBalance: 1, getBalances: 0}, new Set([])],
  'hack2hire:67957d75010c9ed2f849b1fa': ['TransactionSystem', 2, {getBalance: 1, getBalances: 0, getBalanceAfter: 2}, new Set([])],
  'hack2hire:6a121534653f4ff494e2c7ea': ['CameraLogServer', 0, {requestLog: 2, pollCommand: 1, sendLog: 3, pollLog: 0}, new Set(["requestLog", "sendLog"])],
  'hack2hire:689cf810aee746eb1c84ba38': ['CloudStorage', 0, {addFile: 2, copyFile: 2, getFilesize: 1}, new Set([])],
  'hack2hire:689e4cd5735253d430dee92d': ['CloudStorage', 0, {addFile: 2, copyFile: 2, getFilesize: 1, findFile: 2}, new Set([])],
  'hack2hire:689e4cd8735253d430dee92e': ['CloudStorage', 0, {addFile: 2, copyFile: 2, getFilesize: 1, findFile: 2, addUser: 2, addFileBy: 3, mergeUser: 2}, new Set([])],
  'hack2hire:689e4cd9735253d430dee92f': ['CloudStorage', 0, {addFile: 2, copyFile: 2, getFilesize: 1, findFile: 2, addUser: 2, addFileBy: 3, mergeUser: 2, backupUser: 1, restoreUser: 1}, new Set([])],
  'hack2hire:6855e42cc201117d348a2630': ['CustomerRevenueSystem', 0, {insert: 1, insertWithReferrer: 2, getLowestK: 2}, new Set([])],
  'hack2hire:69445eb8867a3f9f539ff53d': ['CustomerRevenueSystem', 0, {insert: 1, insertWithReferrer: 2, getLowestK: 2, getNestedRevenue: 2}, new Set([])],
  'hack2hire:68b93d5483188776facc8ff6': ['ConnectFour', 0, {play: 1}, new Set([])],
  'hack2hire:67a19e53b41c4108d8ccb3d4': ['InMemoryKVDB', 0, {set: 2, get: 1, delete: 1, count: 1, begin: 0, rollback: 0, commit: 0}, new Set(["begin", "delete", "set"])],
  'hack2hire:677ae48578175fce2ecdfc0a': ['DocumentLibrary', 1, {search: 1}, new Set([])]
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
    types.push(value === null ? 'null' : typeof value);
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
  if (packet === null || typeof packet !== 'object' || Array.isArray(packet) || Object.keys(packet).sort().join(',') !== 'calls,native_problem_uid,schema' || packet.schema !== 'gamma.native-class-transport.v1' || typeof packet.native_problem_uid !== 'string' || !Object.hasOwn(LAYOUT, packet.native_problem_uid) || !Array.isArray(packet.calls)) throw Error('fixed argument-only native packet required');
  const transport = require('./transport.cjs');
  const exported = require('./program.cjs');
  for (let i = 0; i < packet.calls.length; i++) {
    let record;
    try { record = {i, ...observe(exported, packet.native_problem_uid, packet.calls[i], transport)}; }
    catch (error) { record = {i, error: String(error).slice(0, 300)}; }
    process.stdout.write(JSON.stringify(record) + '\n');
  }
  process.stdout.write(JSON.stringify({done: packet.calls.length}) + '\n');
}

if (require.main === module) main();
module.exports = {LAYOUT, shape, observe};
