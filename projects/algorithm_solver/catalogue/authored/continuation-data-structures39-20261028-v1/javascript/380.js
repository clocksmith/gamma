"use strict";

class RandomizedSet {
  constructor() {
    this.vals = [];
    this.pos = new Map();
    this._state = 0x9e3779b9 >>> 0;
  }
  _randrange(n) {
    this._state = (Math.imul(this._state, 1664525) + 1013904223) >>> 0;
    return this._state % n;
  }
  insert(val) {
    if (this.pos.has(val)) return false;
    this.pos.set(val, this.vals.length);
    this.vals.push(val);
    return true;
  }
  remove(val) {
    if (!this.pos.has(val)) return false;
    const idx = this.pos.get(val);
    this.pos.delete(val);
    const last = this.vals.pop();
    if (idx < this.vals.length) {
      this.vals[idx] = last;
      this.pos.set(last, idx);
    }
    return true;
  }
  getRandom() {
    return this.vals[this._randrange(this.vals.length)];
  }
}

function solve(operation_names, argument_lists) {
  const instance = new RandomizedSet();
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i];
    const args = argument_lists[i];
    if (op === "insert") out.push(instance.insert(args[0]));
    else if (op === "remove") out.push(instance.remove(args[0]));
    else if (op === "getRandom") out.push(instance.getRandom());
    else throw new Error("unknown operation");
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.RandomizedSet = RandomizedSet;
