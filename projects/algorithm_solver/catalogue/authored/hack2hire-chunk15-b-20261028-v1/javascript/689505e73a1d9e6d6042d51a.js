"use strict";
// Hack2Hire 689505e73a1d9e6d6042d51a (Design In-memory Database with Backup, variant 1 of 4) over an INFERRED spec; qualification unknown.

class InMemoryDB {
  constructor() {
    this.records = new Map();
  }

  setData(key, field, value) {
    let record = this.records.get(key);
    if (record === undefined) {
      record = new Map();
      this.records.set(key, record);
    }
    record.set(field, value);
  }

  getData(key, field) {
    const record = this.records.get(key);
    if (record === undefined || !record.has(field)) return "";
    return record.get(field);
  }

  deleteData(key, field) {
    const record = this.records.get(key);
    if (record === undefined || !record.has(field)) return false;
    record.delete(field);
    if (record.size === 0) this.records.delete(key);
    return true;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "InMemoryDB" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new InMemoryDB(...argumentLists[0]);
  const allowed = new Set(["setData", "getData", "deleteData"]);
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
