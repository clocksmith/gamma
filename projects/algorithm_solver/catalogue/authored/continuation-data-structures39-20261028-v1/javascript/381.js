"use strict";

class RandomizedCollection {
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
    let bucket = this.pos.get(val);
    if (!bucket) {
      bucket = [];
      this.pos.set(val, bucket);
    }
    const isNew = bucket.length === 0;
    bucket.push(this.vals.length);
    this.vals.push([val, bucket.length - 1]);
    return isNew;
  }
  remove(val) {
    const bucket = this.pos.get(val);
    if (!bucket || bucket.length === 0) return false;
    const idx = bucket.pop();
    const last = this.vals.pop();
    if (idx < this.vals.length) {
      this.vals[idx] = last;
      this.pos.get(last[0])[last[1]] = idx;
    }
    return true;
  }
  getRandom() {
    return this.vals[this._randrange(this.vals.length)][0];
  }
}

function solve(operation_names, argument_lists) {
  const instance = new RandomizedCollection();
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
module.exports.RandomizedCollection = RandomizedCollection;
