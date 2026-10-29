'use strict';
// Direct native-class transport for the existing isolated judge; no expectations. Interfaces are INFERRED.
const fs = require('fs');
const APPLY = Reflect.apply, CONSTRUCT = Reflect.construct, PROTOTYPE = Object.getPrototypeOf;
const LAYOUT = {
  'hack2hire:68504f81839fbdf76404b1d1': ['SnapshotSet', {add: 1, remove: 1, contains: 1, getIterator: 0, hasNext: 1, next: 1}, new Set()],
  'hack2hire:69dd8c3595e80ae213e5b9c7': ['ToDoList', {add: 3, get: 1, updateStatus: 2, addDependency: 2, getDependencies: 1}, new Set(['add'])],
  'hack2hire:69dd8d2795e80ae213e5b9cf': ['ToDoList', {add: 3, get: 1, updateStatus: 2, addDependency: 2, getDependencies: 1, getExecutionOrder: 0}, new Set(['add'])],
  'hack2hire:677b491778175fce2ecdfc10': ['FunctionLibrary', {register: 3, findMatches: 1}, new Set(['register'])]
};

function shape(uid, args) {
  if (typeof uid !== 'string' || !Object.hasOwn(LAYOUT, uid) || !Array.isArray(args) || args.length !== 2) throw Error('exact native identity and trace shape required');
  const [name, methods] = LAYOUT[uid], [operations, rows] = args;
  if (!Array.isArray(operations) || !Array.isArray(rows) || !operations.length || operations.length !== rows.length || operations[0] !== name || !Array.isArray(rows[0]) || rows[0].length) throw Error('exact initial constructor required');
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
  const before = transport.encode(args), receiver = CONSTRUCT(NativeClass, []);
  if (PROTOTYPE(receiver) !== NativeClass.prototype) throw Error('native constructor must produce its own instance');
  const outputs = [null], snapshots = [null], types = ['constructed'];
  for (let i = 1; i < args[0].length; i++) {
    const operation = args[0][i], method = NativeClass.prototype[operation];
    if (typeof method !== 'function') throw Error('declared native prototype method missing');
    const value = APPLY(method, receiver, args[1][i]);
    types.push(typeof value);
    const isVoid = LAYOUT[uid][2].has(operation);
    if (isVoid && value !== undefined) throw Error('void method returned a value');
    const normalized = isVoid ? null : value;
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
