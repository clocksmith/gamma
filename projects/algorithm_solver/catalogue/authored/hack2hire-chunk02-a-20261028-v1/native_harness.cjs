'use strict';
// Direct native-class transport for the existing isolated judge; no expectations.
// Adapted from requested-22-a: identities are Hack2Hire uid strings and constructors may take arguments.
const fs = require('fs');
const APPLY = Reflect.apply, CONSTRUCT = Reflect.construct, PROTOTYPE = Object.getPrototypeOf;
const LAYOUT = {
  'hack2hire:69117148869dd6a56c434054': ['CreditSystem', 0, {addCredit: 4, revokeCredit: 2, getBalance: 1}, new Set(['addCredit'])],
  'hack2hire:6913b4310ac116974ccedd13': ['CreditSystem', 0, {addCredit: 4, consumeCredit: 2, getBalance: 1}, new Set(['addCredit'])],
  'hack2hire:684bada44023c4f502877df5': ['IpFirewall', 1, {isAllowed: 1}, new Set()],
  'hack2hire:6a5941a8665efda9311fa417': ['DistinctPIIValuesCounter', 0, {processEvent: 1, getDistinctPIICount: 0}, new Set(['processEvent'])],
  'hack2hire:6a5941f5665efda9311fa41e': ['DistinctPIIValuesCounter', 0, {processEvent: 1, getDistinctPIICount: 0, getSharedPIICount: 0}, new Set(['processEvent'])],
  'hack2hire:67b36a7975074948935624c7': ['MultiStreamReader', 1, {read: 1}, new Set()]
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
  const outputs = [null], snapshots = [null], types = ['constructed'], voids = LAYOUT[uid][3];
  for (let i = 1; i < args[0].length; i++) {
    const operation = args[0][i], method = NativeClass.prototype[operation];
    if (typeof method !== 'function') throw Error('declared native prototype method missing');
    const value = APPLY(method, receiver, args[1][i]);
    types.push(typeof value);
    if (voids.has(operation) && value !== undefined) throw Error('void method returned a value');
    const normalized = voids.has(operation) ? null : value;
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
