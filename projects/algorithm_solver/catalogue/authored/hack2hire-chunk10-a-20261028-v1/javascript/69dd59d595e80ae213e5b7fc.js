"use strict";
// Hack2Hire 69dd59d595e80ae213e5b7fc (Design A Temporal Key-Value Store, variant 2 of 2) over an INFERRED spec; qualification unknown.

function upperBound(a, x) {
  let lo = 0, hi = a.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (a[mid] <= x) lo = mid + 1; else hi = mid; }
  return lo;
}

class TemporalKVStore {
  constructor() { this.versions = new Map(); } // key -> {times: increasing, values: parallel; null marks a deletion}

  _write(key, value, timestamp) {
    const v = this.versions.get(key);
    if (v === undefined) this.versions.set(key, {times: [timestamp], values: [value]});
    else if (v.times[v.times.length - 1] === timestamp) v.values[v.values.length - 1] = value;
    else { v.times.push(timestamp); v.values.push(value); }
  }

  set(key, value, timestamp) { this._write(key, value, timestamp); }

  get(key, timestamp) {
    const v = this.versions.get(key);
    if (v === undefined) return "";
    const i = upperBound(v.times, timestamp);
    if (i === 0) return "";
    const value = v.values[i - 1];
    return value === null ? "" : value;
  }

  remove(key, timestamp) {
    const visible = this.get(key, timestamp) !== "";
    this._write(key, null, timestamp);
    return visible;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "TemporalKVStore" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new TemporalKVStore(...argumentLists[0]);
  const allowed = new Set(["set", "get", "remove"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.TemporalKVStore = TemporalKVStore;
