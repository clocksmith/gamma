'use strict';

// 588. Design In-Memory File System.

class _Entry {
  constructor() { this.children = new Map(); this.isFile = false; this.parts = []; }
}
class FileSystem {
  constructor() { this.root = new _Entry(); }
  _lookup(path, create = false) {
    let node = this.root;
    for (const name of path.split('/')) {
      if (!name) continue;
      if (create && !node.children.has(name)) node.children.set(name, new _Entry());
      node = node.children.get(name);
    }
    return node;
  }
  ls(path) {
    const node = this._lookup(path);
    return node.isFile ? [path.slice(path.lastIndexOf('/') + 1)] : Array.from(node.children.keys()).sort();
  }
  mkdir(path) { this._lookup(path, true); }
  addContentToFile(filePath, content) {
    const node = this._lookup(filePath, true); node.isFile = true; node.parts.push(content);
  }
  readContentFromFile(filePath) { return this._lookup(filePath).parts.join(''); }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new FileSystem(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

const Solution = FileSystem;

if (typeof module !== 'undefined') module.exports = { solve, FileSystem, Solution };
