"use strict";
// Hack2Hire 689641c83a1d9e6d6042d585 (Design In-memory Database with Backup, variant 3 of 4) over an INFERRED spec; qualification unknown.

class InMemoryDB {
  constructor() {
    this.records = new Map();
  }

  _put(key, field, value, expiry) {
    let record = this.records.get(key);
    if (record === undefined) {
      record = new Map();
      this.records.set(key, record);
    }
    record.set(field, [value, expiry]);
  }

  _live(key, field, timestamp) {
    const record = this.records.get(key);
    if (record === undefined) return null;
    const item = record.get(field);
    if (item === undefined || (item[1] !== null && timestamp >= item[1])) return null;
    return item;
  }

  setDataAt(key, field, value, timestamp) {
    this._put(key, field, value, null);
  }

  setDataAtWithTtl(key, field, value, timestamp, ttl) {
    this._put(key, field, value, timestamp + ttl);
  }

  getDataAt(key, field, timestamp) {
    const item = this._live(key, field, timestamp);
    return item === null ? "" : item[0];
  }

  deleteDataAt(key, field, timestamp) {
    const record = this.records.get(key);
    if (record === undefined || !record.has(field)) return false;
    const alive = this._live(key, field, timestamp) !== null;
    record.delete(field);
    if (record.size === 0) this.records.delete(key);
    return alive;
  }

  scanDataAt(key, timestamp) {
    return this.scanDataByPrefixAt(key, "", timestamp);
  }

  scanDataByPrefixAt(key, prefix, timestamp) {
    const record = this.records.get(key);
    if (record === undefined) return [];
    const names = [];
    for (const [f, item] of record) if (f.startsWith(prefix) && (item[1] === null || timestamp < item[1])) names.push(f);
    names.sort();
    return names.map((f) => f + "(" + record.get(f)[0] + ")");
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "InMemoryDB" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new InMemoryDB(...argumentLists[0]);
  const allowed = new Set(["setDataAt", "setDataAtWithTtl", "deleteDataAt", "getDataAt", "scanDataAt", "scanDataByPrefixAt"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.InMemoryDB = InMemoryDB;
