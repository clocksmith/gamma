// Original hack2hire:680e4d4d7003ce5d1dcb037e; inferred public-preview contract; qualification unknown.
"use strict";
class LRUCache {
  constructor(capacity) { this.capacity = capacity; this.values = new Map(); }
  _evict() { while (this.values.size > this.capacity) this.values.delete(this.values.keys().next().value); }
  get(key) { if (!this.values.has(key)) return -1; const value = this.values.get(key); this.values.delete(key); this.values.set(key,value); return structuredClone(value); }
  put(key,value) { this.values.delete(key); this.values.set(key,structuredClone(value)); this._evict(); }
  resize(capacity) { this.capacity = capacity; this._evict(); }
}

function solve(operationNames, argumentLists) {
  if (!operationNames.length || operationNames.length !== argumentLists.length || operationNames[0] !== "LRUCache") throw new Error("exact constructor trace required");
  const instance = new LRUCache(...argumentLists[0]), result = [null], allowed = new Set(["get", "put", "resize"]);
  for (let i = 1; i < operationNames.length; i++) { if (!allowed.has(operationNames[i])) throw new Error("unknown method"); result.push(instance[operationNames[i]](...argumentLists[i]) ?? null); }
  return result;
}
module.exports = solve;
module.exports.LRUCache = LRUCache;
