'use strict';
// Direct native-class transport for the existing isolated judge; no expectations (hack2hire-chunk02-d, INFERRED interfaces).
const fs = require('fs');
const APPLY = Reflect.apply, CONSTRUCT = Reflect.construct, PROTOTYPE = Object.getPrototypeOf;
// uid -> [class name, constructor arity, {method: arity}, void methods]
const LAYOUT = {
  "hack2hire:694af9676e481a4b09cbc77d": ["ModSystem", 1, {canRemove: 2}, new Set([])],
  "hack2hire:694b056e6e481a4b09cbc7e4": ["ModSystem", 1, {canRemove: 2, getModerators: 0}, new Set([])],
  "hack2hire:694b08dc6e481a4b09cbc807": ["ModSystem", 1, {canRemove: 2, getModerators: 0, canRemoveAt: 3, getModeratorsAt: 1}, new Set([])],
  "hack2hire:6ac95215339e3a32c154ddc3": ["RectangleBoard", 2, {addRectangle: 4, getTopRectangle: 2}, new Set([])],
  "hack2hire:6ac95252339e3a32c154ddc8": ["RectangleBoard", 2, {addRectangle: 4, getTopRectangle: 2, removeRectangle: 1}, new Set([])],
  "hack2hire:6ac95279339e3a32c154ddca": ["RectangleBoard", 2, {addRectangle: 4, getTopRectangle: 2, removeRectangle: 1, bringToFront: 1}, new Set([])],
  "hack2hire:6ac952f0339e3a32c154ddd2": ["RectangleBoard", 2, {addRectangle: 4, getTopRectangle: 2, removeRectangle: 1, bringToFront: 1, undo: 0}, new Set([])],
  "hack2hire:69f78c6830f41dfd539fc6dc": ["Spreadsheet", 0, {setCell: 2, getCell: 1, resetCell: 1}, new Set(["setCell", "resetCell"])],
  "hack2hire:69f78ced30f41dfd539fc6e1": ["Spreadsheet", 0, {setCell: 2, getCell: 1, resetCell: 1}, new Set(["resetCell"])],
  "hack2hire:6ab32819e74ebb7457a3f0f5": ["WorkQueue", 3, {reserve: 1, complete: 2, fail: 2, getDeadLetters: 1}, new Set([])],
  "hack2hire:6ab328bbe74ebb7457a3f0fc": ["WorkQueue", 4, {reserve: 1, complete: 2, fail: 2, getDeadLetters: 1}, new Set([])],
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
