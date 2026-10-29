"use strict";
// Hack2Hire 689bb2061126a03aace65e39 (Design In-memory Database with Backup, variant 4 of 4) over an INFERRED spec; qualification unknown.

class InMemoryDB {
  constructor() {
    this.records = new Map();
    this.backups = [];
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

  backup(timestamp) {
    const snapshot = new Map();
    for (const [key, record] of this.records) {
      const kept = new Map();
      for (const [field, [value, expiry]] of record) {
        if (expiry === null) kept.set(field, [value, null]);
        else if (timestamp < expiry) kept.set(field, [value, expiry - timestamp]);
      }
      if (kept.size) snapshot.set(key, kept);
    }
    this.backups.push([timestamp, snapshot]);
    return snapshot.size;
  }

  restore(timestamp, timestampToRestore) {
    let lo = 0, hi = this.backups.length;
    while (lo < hi) {
      const mid = (lo + hi) >> 1;
      if (this.backups[mid][0] <= timestampToRestore) lo = mid + 1;
      else hi = mid;
    }
    const snapshot = this.backups[lo - 1][1];
    this.records = new Map();
    for (const [key, kept] of snapshot) {
      const record = new Map();
      for (const [f, [v, r]] of kept) record.set(f, [v, r === null ? null : timestamp + r]);
      this.records.set(key, record);
    }
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "InMemoryDB" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new InMemoryDB(...argumentLists[0]);
  const allowed = new Set(["setDataAt", "setDataAtWithTtl", "deleteDataAt", "getDataAt", "scanDataAt", "scanDataByPrefixAt", "backup", "restore"]);
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
