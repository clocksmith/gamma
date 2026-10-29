"use strict";
// Original Hack2Hire 677b491778175fce2ecdfc10 native class variant over an INFERRED specification, with a separately declared trace adapter; qualification unknown.
const keyOf = (types) => types.length + ":" + types.join(",");
class FunctionLibrary {
  constructor() { this.exact = new Map(); this.variadic = new Map(); }
  register(name, argumentTypes, isVariadic) {
    const table = isVariadic ? this.variadic : this.exact, key = keyOf(argumentTypes);
    if (!table.has(key)) table.set(key, []);
    table.get(key).push(name);
  }
  findMatches(argumentTypes) {
    const args = argumentTypes, found = [...(this.exact.get(keyOf(args)) || [])];
    if (args.length) {
      let start = args.length - 1;
      while (start > 0 && args[start - 1] === args[args.length - 1]) start--;
      for (let k = start + 1; k <= args.length; k++) found.push(...(this.variadic.get(keyOf(args.slice(0, k))) || []));
    }
    return found.sort();
  }
}
function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "FunctionLibrary" || argumentLists[0].length !== 0) throw new Error("exact constructor required");
  const instance = new FunctionLibrary(), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (operationNames[i] !== "register" && operationNames[i] !== "findMatches") throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.FunctionLibrary = FunctionLibrary;
