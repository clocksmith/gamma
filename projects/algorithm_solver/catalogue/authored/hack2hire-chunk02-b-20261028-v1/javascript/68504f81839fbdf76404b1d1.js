"use strict";
// Original Hack2Hire 68504f81839fbdf76404b1d1 native class variant over an INFERRED specification, with a separately declared trace adapter; qualification unknown.
class SnapshotSet {
  constructor() {
    this.entries = [];          // [value, removedAtVersion]
    this.position = new Map();  // live value -> entry index
    this.version = 0;
    this.iterators = [];        // [version, end, cursor]
  }
  add(value) {
    if (this.position.has(value)) return false;
    this.version++;
    this.position.set(value, this.entries.length);
    this.entries.push([value, Infinity]);
    return true;
  }
  remove(value) {
    if (!this.position.has(value)) return false;
    this.version++;
    this.entries[this.position.get(value)][1] = this.version;
    this.position.delete(value);
    return true;
  }
  contains(value) { return this.position.has(value); }
  getIterator() { this.iterators.push([this.version, this.entries.length, 0]); return this.iterators.length - 1; }
  hasNext(iteratorId) {
    const it = this.iterators[iteratorId];
    while (it[2] < it[1] && this.entries[it[2]][1] <= it[0]) it[2]++;
    return it[2] < it[1];
  }
  next(iteratorId) {
    if (!this.hasNext(iteratorId)) throw new Error("iterator exhausted");
    const it = this.iterators[iteratorId];
    return this.entries[it[2]++][0];
  }
}
const METHODS = new Set(["add", "remove", "contains", "getIterator", "hasNext", "next"]);
function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "SnapshotSet" || argumentLists[0].length !== 0) throw new Error("exact constructor required");
  const instance = new SnapshotSet(), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!METHODS.has(operationNames[i])) throw new Error("unknown method");
    result.push(instance[operationNames[i]](...argumentLists[i]));
  }
  return result;
}
module.exports = solve;
module.exports.SnapshotSet = SnapshotSet;
