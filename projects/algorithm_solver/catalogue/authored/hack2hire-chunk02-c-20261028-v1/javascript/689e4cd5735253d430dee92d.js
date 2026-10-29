"use strict";
// Hack2Hire 689e4cd5735253d430dee92d (Cloud Storage System, variant 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
function lowerBound(sorted, key) {
  let lo = 0, hi = sorted.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (sorted[mid] < key) lo = mid + 1; else hi = mid; }
  return lo;
}
class CloudStorage {
  constructor() {
    this.files = new Map(); // name -> [size, owner]; owner null = unlimited admin
    this.names = []; // sorted file names, rebuilt lazily when namesStale
    this.namesStale = false;
    this.capacity = new Map();
    this.used = new Map();
    this.owned = new Map();
    this.backups = new Map();
  }
  addFile(name, size) {
    if (this.files.has(name)) return false;
    this.store(name, size, null);
    return true;
  }
  store(name, size, owner) {
    this.files.set(name, [size, owner]);
    if (!this.namesStale) this.names.splice(lowerBound(this.names, name), 0, name);
  }
  copyFile(nameFrom, nameTo) {
    const source = this.files.get(nameFrom);
    if (source === undefined || this.files.has(nameTo)) return false;
    const [size, owner] = source;
    if (owner !== null) {
      if (this.used.get(owner) + size > this.capacity.get(owner)) return false;
      this.used.set(owner, this.used.get(owner) + size);
      this.owned.get(owner).add(nameTo);
    }
    this.store(nameTo, size, owner);
    return true;
  }
  getFilesize(name) {
    const entry = this.files.get(name);
    return entry === undefined ? -1 : entry[0];
  }
  findFile(prefix, suffix) {
    if (this.namesStale) { this.names = [...this.files.keys()].sort(); this.namesStale = false; }
    const hits = [];
    for (let i = lowerBound(this.names, prefix); i < this.names.length && this.names[i].startsWith(prefix); i++) {
      const name = this.names[i];
      if (name.endsWith(suffix)) hits.push([this.files.get(name)[0], name]);
    }
    hits.sort((a, b) => b[0] - a[0] || (a[1] < b[1] ? -1 : a[1] > b[1] ? 1 : 0));
    return hits.map(([size, name]) => name + "(" + size + ")");
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "CloudStorage") throw new Error("exact initial constructor required");
  const instance = new CloudStorage(...argumentLists[0]);
  const allowed = new Set(["addFile", "copyFile", "getFilesize", "findFile"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.CloudStorage = CloudStorage;
