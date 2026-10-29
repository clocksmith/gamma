'use strict';
const fs = require('fs');
const APPLY = Reflect.apply, CONSTRUCT = Reflect.construct, PROTOTYPE = Object.getPrototypeOf;
// uid -> [class name, constructor arity, {method: arity}, void methods normalised to null]
const LAYOUT = {
  "hack2hire:687c3a5eaa2b26b0b64b39e5": ["BankingSystem", 0, {"createAccount": 2, "deposit": 3, "transfer": 4}, new Set([])],
  "hack2hire:687c4741aa2b26b0b64b39ee": ["BankingSystem", 0, {"createAccount": 2, "deposit": 3, "transfer": 4, "topSpenders": 2}, new Set([])],
  "hack2hire:687c4e56024483ac76db8c9b": ["BankingSystem", 0, {"createAccount": 2, "deposit": 3, "transfer": 4, "topSpenders": 2, "pay": 3, "getPaymentStatus": 3}, new Set([])],
  "hack2hire:687c5c0b024483ac76db8ca2": ["BankingSystem", 0, {"createAccount": 2, "deposit": 3, "transfer": 4, "topSpenders": 2, "pay": 3, "getPaymentStatus": 3, "mergeAccounts": 3, "getBalance": 3}, new Set([])],
  "hack2hire:69178d9a10632c00111ca20d": ["DeliverySystem", 0, {"addDriver": 2, "addDelivery": 3, "getTotalCost": 0}, new Set(["addDelivery", "addDriver"])],
  "hack2hire:6917944e10632c00111ca217": ["DeliverySystem", 0, {"addDriver": 2, "addDelivery": 3, "getTotalCost": 0, "payUpTo": 1, "getTotalCostUnpaid": 0}, new Set(["addDelivery", "addDriver", "payUpTo"])],
  "hack2hire:6917944f10632c00111ca218": ["DeliverySystem", 0, {"addDriver": 2, "addDelivery": 3, "getTotalCost": 0, "payUpTo": 1, "getTotalCostUnpaid": 0, "getMaxActiveDriversInLast24Hours": 1}, new Set(["addDelivery", "addDriver", "payUpTo"])],
  "hack2hire:69c19a8521f6ab4226964bf7": ["ConnectKGame", 1, {"placePiece": 2}, new Set([])],
  "hack2hire:69d16c5617b72775cc49bf93": ["Document", 0, {"setProperty": 3, "getProperty": 2, "undo": 0}, new Set(["setProperty"])],
  "hack2hire:69d1730e17b72775cc49bfc6": ["Document", 0, {"setProperty": 3, "getProperty": 2, "undo": 0, "redo": 0}, new Set(["setProperty"])],
  "hack2hire:69d1735f17b72775cc49bfc7": ["Document", 0, {"setProperty": 3, "getProperty": 2, "undo": 0, "redo": 0, "removeProperty": 2, "getProperties": 1}, new Set(["setProperty"])],
  "hack2hire:6941be52b9d646bec48c68cc": ["TennisGame", 0, {"pointTo": 1, "getPoints": 0, "getScore": 0, "getWinner": 0}, new Set(["pointTo"])],
  "hack2hire:6941c912e79fe20cf9ff4435": ["TennisSet", 0, {"pointTo": 1, "getGames": 0, "getGameScore": 0, "getWinner": 0}, new Set(["pointTo"])],
  "hack2hire:683e86418d3dfb7c9bd756ab": ["FileSystem", 0, {"addFile": 2, "find": 2}, new Set(["addFile"])],
  "hack2hire:683f1dc68d3dfb7c9bd756da": ["FileSystem", 0, {"addFile": 2, "find": 2}, new Set(["addFile"])]
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
