'use strict';
// Direct native-class transport for the existing isolated judge; no expectations (hack2hire-chunk15-b, INFERRED interfaces).
const fs = require('fs');
const APPLY = Reflect.apply, CONSTRUCT = Reflect.construct, PROTOTYPE = Object.getPrototypeOf;
// uid -> [class name, constructor arity, {method: arity}, void methods]
const LAYOUT = {
  "hack2hire:689505e73a1d9e6d6042d51a": ["InMemoryDB", 0, {setData: 3, getData: 2, deleteData: 2}, new Set(["setData"])],
  "hack2hire:68961c873a1d9e6d6042d57a": ["InMemoryDB", 0, {setData: 3, getData: 2, deleteData: 2, scanData: 1, scanDataByPrefix: 2}, new Set(["setData"])],
  "hack2hire:689641c83a1d9e6d6042d585": ["InMemoryDB", 0, {setDataAt: 4, setDataAtWithTtl: 5, deleteDataAt: 3, getDataAt: 3, scanDataAt: 2, scanDataByPrefixAt: 3}, new Set(["setDataAt", "setDataAtWithTtl"])],
  "hack2hire:689bb2061126a03aace65e39": ["InMemoryDB", 0, {setDataAt: 4, setDataAtWithTtl: 5, deleteDataAt: 3, getDataAt: 3, scanDataAt: 2, scanDataByPrefixAt: 3, backup: 1, restore: 2}, new Set(["setDataAt", "setDataAtWithTtl", "restore"])],
  "hack2hire:677df76b052a260e0165706c": ["InfiniteQueue", 0, {add: 1, poll: 0, getRandom: 1}, new Set(["add"])],
  "hack2hire:68539b6bd3dbd4fb8b026e9f": ["LazyArray", 1, {map: 2, indexOf: 1}, new Set(["map"])],
  "hack2hire:681bc967a73bd75b806cb994": ["EscapeRoom", 2, {advance: 1, countInRoom: 1, topPlayers: 1}, new Set(["advance"])],
  "hack2hire:68edc9c15abdefad4f6693fc": ["EventLogger", 1, {logEvent: 2}, new Set([])],
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
