"use strict";
// Hack2Hire 6778936c775a4a31045ead0e (Windowed Key-Value Store, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
class WindowedKeyValueStore {
  constructor(capacity, windowSize) {
    this.capacity = capacity;
    this.windowSize = windowSize;
    this.entries = new Map(); // key -> [value, time]; insertion order = least to most recently used
  }
  put(key, val, time) {
    this.entries.delete(key);
    this.entries.set(key, [val, time]);
    if (this.entries.size > this.capacity) this.entries.delete(this.entries.keys().next().value);
  }
  get(key, time) {
    const entry = this.entries.get(key);
    if (entry === undefined || time - entry[1] >= this.windowSize) return -1;
    this.entries.delete(key);
    this.entries.set(key, entry);
    return entry[0];
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "WindowedKeyValueStore") throw new Error("exact initial constructor required");
  const instance = new WindowedKeyValueStore(...argumentLists[0]);
  const allowed = new Set(["put", "get"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.WindowedKeyValueStore = WindowedKeyValueStore;
