// Original hack2hire:678365c4d0faf7ec64cc3ad9; inferred public-preview contract; qualification unknown.
"use strict";
class PathKeyValueStore {
  constructor() { this.values = new Map([['/','root']]); this.children = new Map([['/',0]]); }
  _parent(path) { return path.slice(0, path.lastIndexOf('/')) || '/'; }
  create(path, value) {
    const parent = this._parent(path);
    if (this.values.has(path) || !this.values.has(parent)) return false;
    this.values.set(path, value); this.children.set(path, 0); this.children.set(parent, this.children.get(parent)+1); return true;
  }
  set(path, value) { if (path === '/' || !this.values.has(path)) return false; this.values.set(path, value); return true; }
  get(path) { return this.values.has(path) ? this.values.get(path) : null; }
  delete(path) {
    if (path === '/' || !this.values.has(path) || this.children.get(path)) return false;
    const parent = this._parent(path); this.children.set(parent, this.children.get(parent)-1); this.values.delete(path); this.children.delete(path); return true;
  }
}

function solve(operationNames, argumentLists) {
  if (!operationNames.length || operationNames.length !== argumentLists.length || operationNames[0] !== "PathKeyValueStore") throw new Error("exact constructor trace required");
  const instance = new PathKeyValueStore(...argumentLists[0]), result = [null], allowed = new Set(["create", "set", "get", "delete"]);
  for (let i = 1; i < operationNames.length; i++) { if (!allowed.has(operationNames[i])) throw new Error("unknown method"); result.push(instance[operationNames[i]](...argumentLists[i]) ?? null); }
  return result;
}
module.exports = solve;
module.exports.PathKeyValueStore = PathKeyValueStore;
