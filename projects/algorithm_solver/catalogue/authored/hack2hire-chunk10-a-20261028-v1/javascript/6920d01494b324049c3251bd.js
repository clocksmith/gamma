"use strict";
// Hack2Hire 6920d01494b324049c3251bd (Design KV Store with Rollback, variant 1 of 3) over an INFERRED spec; qualification unknown.

class KeyValueStore {
  constructor() { this.data = new Map(); }
  set(key, value) { this.data.set(key, value); }
  get(key) { const v = this.data.get(key); return v === undefined ? "" : v; }
  unset(key) { this.data.delete(key); }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "KeyValueStore" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new KeyValueStore(...argumentLists[0]);
  const allowed = new Set(["set", "get", "unset"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.KeyValueStore = KeyValueStore;
