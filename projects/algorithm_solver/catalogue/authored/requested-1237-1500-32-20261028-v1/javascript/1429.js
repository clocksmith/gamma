"use strict";

class FirstUnique {
  constructor(nums) {
    this.unique = new Set();
    this.seen = new Set();
    for (let i = 0; i < nums.length; i++) this.add(nums[i]);
  }
  showFirstUnique() {
    if (this.unique.size === 0) return -1;
    return this.unique.values().next().value;
  }
  add(value) {
    if (!this.seen.has(value)) {
      this.seen.add(value);
      this.unique.add(value);
    } else {
      this.unique.delete(value);
    }
  }
}

function solve(operation_names, argument_lists) {
  const inst = new FirstUnique(argument_lists[0][0]);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i], args = argument_lists[i];
    if (op === "add") { inst.add(args[0]); out.push(null); }
    else out.push(inst.showFirstUnique());
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.FirstUnique = FirstUnique;
