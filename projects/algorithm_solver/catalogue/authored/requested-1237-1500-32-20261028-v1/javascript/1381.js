"use strict";

class CustomStack {
  constructor(maxSize) {
    this.cap = maxSize;
    this.stk = [];
    this.inc = new Int32Array(maxSize);
  }
  push(x) {
    if (this.stk.length < this.cap) this.stk.push(x);
  }
  pop() {
    if (this.stk.length === 0) return -1;
    const i = this.stk.length - 1;
    const add = this.inc[i];
    if (i > 0) this.inc[i - 1] += add;
    this.inc[i] = 0;
    return this.stk.pop() + add;
  }
  increment(k, val) {
    const idx = Math.min(k, this.stk.length) - 1;
    if (idx >= 0) this.inc[idx] += val;
  }
}

function solve(operation_names, argument_lists) {
  const inst = new CustomStack(argument_lists[0][0]);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i], args = argument_lists[i];
    if (op === "push") { inst.push(args[0]); out.push(null); }
    else if (op === "pop") out.push(inst.pop());
    else { inst.increment(args[0], args[1]); out.push(null); }
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.CustomStack = CustomStack;
