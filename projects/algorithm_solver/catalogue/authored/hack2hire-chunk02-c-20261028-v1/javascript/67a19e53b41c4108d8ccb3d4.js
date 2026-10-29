"use strict";
// Hack2Hire 67a19e53b41c4108d8ccb3d4 (Design In-Memory Key-Value Database, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
const ABSENT = Symbol("absent");
class InMemoryKVDB {
  constructor() {
    this.data = new Map();
    this.counts = new Map();
    this.undo = []; // one Map per open transaction: key -> value before the transaction touched it
  }
  write(key, value) {
    const log = this.undo[this.undo.length - 1];
    if (log && !log.has(key)) log.set(key, this.data.has(key) ? this.data.get(key) : ABSENT);
    if (this.data.has(key)) {
      const old = this.data.get(key);
      this.counts.set(old, this.counts.get(old) - 1);
      this.data.delete(key);
    }
    if (value !== ABSENT) {
      this.data.set(key, value);
      this.counts.set(value, (this.counts.get(value) || 0) + 1);
    }
  }
  set(key, value) { this.write(key, value); }
  get(key) { return this.data.has(key) ? this.data.get(key) : null; }
  delete(key) { if (this.data.has(key)) this.write(key, ABSENT); }
  count(value) { return this.counts.get(value) || 0; }
  begin() { this.undo.push(new Map()); }
  rollback() {
    if (!this.undo.length) return false;
    const log = this.undo.pop(), saved = this.undo;
    this.undo = [];
    for (const [key, value] of log) this.write(key, value);
    this.undo = saved;
    return true;
  }
  commit() {
    if (!this.undo.length) return false;
    this.undo = [];
    return true;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "InMemoryKVDB") throw new Error("exact initial constructor required");
  const instance = new InMemoryKVDB(...argumentLists[0]);
  const allowed = new Set(["set", "get", "delete", "count", "begin", "rollback", "commit"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.InMemoryKVDB = InMemoryKVDB;
