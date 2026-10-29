"use strict";
// Hack2Hire 677f4db36fee41e51af73dd6 (Persistent Stack) over an INFERRED spec; qualification unknown.

class PStack {
  constructor() {
    // version v is the top node of a shared singly linked list; node 0 is the empty stack
    this.parent = [0];
    this.value = [0];
    this.length = [0];
  }

  push(version, val) {
    this.parent.push(version);
    this.value.push(val);
    this.length.push(this.length[version] + 1);
    return this.parent.length - 1;
  }

  pop(version) { return this.parent[version]; }

  peek(version) { return this.value[version]; }

  size(version) { return this.length[version]; }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "PStack" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new PStack(...argumentLists[0]);
  const allowed = new Set(["push", "pop", "peek", "size"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    result.push(instance[operationNames[i]](...argumentLists[i]));
  }
  return result;
}

module.exports = solve;
module.exports.PStack = PStack;
