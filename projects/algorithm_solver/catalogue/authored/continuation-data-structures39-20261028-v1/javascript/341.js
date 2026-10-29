"use strict";

function isIntElem(x) {
  if (x && typeof x.isInteger === "function") return x.isInteger();
  return typeof x === "number";
}

function getIntElem(x) {
  if (x && typeof x.getInteger === "function") return x.getInteger();
  return x;
}

function getListElem(x) {
  if (x && typeof x.getList === "function") return x.getList();
  return x;
}

class NestedIterator {
  constructor(nestedList) {
    this.stack = [];
    for (let i = nestedList.length - 1; i >= 0; i--) {
      this.stack.push(nestedList[i]);
    }
  }
  hasNext() {
    while (this.stack.length > 0) {
      const top = this.stack[this.stack.length - 1];
      if (isIntElem(top)) return true;
      this.stack.pop();
      const sub = getListElem(top);
      for (let i = sub.length - 1; i >= 0; i--) {
        this.stack.push(sub[i]);
      }
    }
    return false;
  }
  next() {
    this.hasNext();
    return getIntElem(this.stack.pop());
  }
}

function solve(operation_names, argument_lists) {
  if (argument_lists === undefined) {
    const it = new NestedIterator(operation_names);
    const out = [];
    while (it.hasNext()) out.push(it.next());
    return out;
  }
  const instance = new NestedIterator(argument_lists[0][0]);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i];
    if (op === "hasNext") out.push(instance.hasNext());
    else if (op === "next") out.push(instance.next());
    else throw new Error("unknown operation");
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.NestedIterator = NestedIterator;
