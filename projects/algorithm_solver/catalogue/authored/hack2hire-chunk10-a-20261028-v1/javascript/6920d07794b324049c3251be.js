"use strict";
// Hack2Hire 6920d07794b324049c3251be (Design KV Store with Rollback, variant 2 of 3) over an INFERRED spec; qualification unknown.

class KeyValueStore {
  constructor() {
    this.data = new Map();
    this.logs = []; // one undo log (key -> old value or null) per open transaction
  }

  _apply(key, value) {
    if (value === null) this.data.delete(key); else this.data.set(key, value);
  }

  _assign(key, value) {
    if (this.logs.length) {
      const log = this.logs[this.logs.length - 1];
      if (!log.has(key)) log.set(key, this.data.has(key) ? this.data.get(key) : null); // first change in this transaction
    }
    this._apply(key, value);
  }

  set(key, value) { this._assign(key, value); }
  get(key) { const v = this.data.get(key); return v === undefined ? "" : v; }
  unset(key) { this._assign(key, null); }
  begin() { this.logs.push(new Map()); }

  rollback() {
    if (!this.logs.length) return false;
    for (const [key, old] of this.logs.pop()) this._apply(key, old);
    return true;
  }

  commit() {
    if (!this.logs.length) return false;
    this.logs = [];
    return true;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "KeyValueStore" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new KeyValueStore(...argumentLists[0]);
  const allowed = new Set(["set", "get", "unset", "begin", "rollback", "commit"]);
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
