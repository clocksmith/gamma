"use strict";
// Hack2Hire 68099e1fcbb5948f87732b56 (KV Store with Prefix Search) over an INFERRED spec; qualification unknown.

class KVStore {
  constructor() {
    this.values = new Map();
    this.root = {children: new Map(), count: 0, end: false}; // trie node: live keys below, key ends here
  }

  set(key, value) {
    this.values.set(key, value);
    let node = this.root;
    node.count++;
    for (const ch of key) {
      let child = node.children.get(ch);
      if (child === undefined) { child = {children: new Map(), count: 0, end: false}; node.children.set(ch, child); }
      child.count++;
      node = child;
    }
    node.end = true;
  }

  get(key) { return this.values.has(key) ? this.values.get(key) : -1; }

  update(key, value) { this.values.set(key, value); }

  deleteKey(key) {
    if (!this.values.has(key)) return;
    this.values.delete(key);
    let node = this.root;
    node.count--;
    for (const ch of key) {
      const child = node.children.get(ch);
      child.count--;
      if (child.count === 0) { node.children.delete(ch); return; } // prune the now-empty branch
      node = child;
    }
    node.end = false;
  }

  prefixSearch(prefix) {
    let node = this.root;
    for (const ch of prefix) {
      node = node.children.get(ch);
      if (node === undefined) return [];
    }
    const out = [], stack = [[node, prefix]];
    while (stack.length > 0) {
      const [current, path] = stack.pop();
      if (current.end) out.push(this.values.get(path));
      const letters = [...current.children.keys()].sort();
      for (let i = letters.length - 1; i >= 0; i--) stack.push([current.children.get(letters[i]), path + letters[i]]);
    }
    return out;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "KVStore" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new KVStore(...argumentLists[0]);
  const allowed = new Set(["set", "get", "update", "deleteKey", "prefixSearch"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.KVStore = KVStore;
