"use strict";
// Hack2Hire 683e86418d3dfb7c9bd756ab (Design Unix Find Command, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
function leaf(spec) {
  const [kind, operand] = spec;
  if (kind === "sizeGreaterThan") return (name, size) => size > operand;
  if (kind === "extension") return (name, size) => { const dot = name.lastIndexOf("."); return (dot < 0 ? "" : name.slice(dot + 1)) === operand; };
  if (kind === "namePrefix") return (name) => name.startsWith(operand);
  throw new Error("unknown filter");
}
class FileSystem {
  constructor() { this.root = {directories: new Map(), files: new Map()}; }
  addFile(path, size) {
    const parts = path.split("/").slice(1);
    let node = this.root;
    for (const part of parts.slice(0, -1)) {
      if (!node.directories.has(part)) node.directories.set(part, {directories: new Map(), files: new Map()});
      node = node.directories.get(part);
    }
    node.files.set(parts[parts.length - 1], [size, path]); // full path kept so queries do not rebuild it
  }
  find(directory, filters) {
    const tests = filters.map(leaf), accept = (name, size) => tests.every((test) => test(name, size));
    let node = this.root;
    if (directory !== "/") {
      for (const part of directory.split("/").slice(1)) {
        node = node.directories.get(part);
        if (node === undefined) return [];
      }
    }
    const found = [], stack = [node];
    while (stack.length) {
      const current = stack.pop();
      for (const [name, entry] of current.files) if (accept(name, entry[0])) found.push(entry[1]);
      for (const child of current.directories.values()) stack.push(child);
    }
    return found.sort();
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "FileSystem" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new FileSystem(...argumentLists[0]), allowed = new Set(["addFile", "find"]), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.FileSystem = FileSystem;
