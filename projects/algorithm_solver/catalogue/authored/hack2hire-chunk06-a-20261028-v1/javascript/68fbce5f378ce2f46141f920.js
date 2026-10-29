"use strict";
// Hack2Hire 68fbce5f378ce2f46141f920 (File System Collection) over an INFERRED spec; qualification unknown.

const cmp = (a, b) => (a < b ? -1 : a > b ? 1 : 0);

class FileSystemStats {
  constructor(files) {
    this.total = 0; this.direct = new Map();
    for (const record of files) {
      const parts = record.split(','), size = Number(parts[1]);
      this.total += size;
      for (const collection of new Set(parts.slice(2))) this.direct.set(collection, (this.direct.get(collection) || 0) + size);
    }
    this.ranked = Array.from(this.direct.keys()).sort((a, b) => this.direct.get(b) - this.direct.get(a) || cmp(a, b));
    this.parent = new Map(); this.hierarchy = new Map(this.direct);
  }

  getTotalSize() { return this.total; }

  getCollectionSize(collectionId) { return this.direct.get(collectionId) || 0; }

  getTopCollections(k) { return this.ranked.slice(0, k); }

  setParent(childId, parentId) {
    const add = this.hierarchy.get(childId) || 0;
    this.parent.set(childId, parentId);
    for (let node = parentId; node !== undefined; node = this.parent.get(node)) this.hierarchy.set(node, (this.hierarchy.get(node) || 0) + add);
  }

  getHierarchySize(collectionId) { return this.hierarchy.get(collectionId) || 0; }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "FileSystemStats" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new FileSystemStats(...argumentLists[0]);
  const allowed = new Set(["getTotalSize", "getCollectionSize", "getTopCollections", "setParent", "getHierarchySize"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.FileSystemStats = FileSystemStats;
