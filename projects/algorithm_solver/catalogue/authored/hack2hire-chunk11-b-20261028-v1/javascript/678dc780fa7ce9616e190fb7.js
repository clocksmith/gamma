"use strict";
// Hack2Hire 678dc780fa7ce9616e190fb7 (Iterator with Filter) over an INFERRED spec; qualification unknown.

const PREDICATES = {
  even: (v) => v % 2 === 0,
  odd: (v) => v % 2 !== 0,
  positive: (v) => v > 0,
  negative: (v) => v < 0,
  nonzero: (v) => v !== 0,
};

class FilterIterator {
  constructor(nums, filterName) {
    this.nums = nums; // read only
    this.accept = PREDICATES[filterName];
    this.i = 0;
  }

  hasNext() {
    while (this.i < this.nums.length && !this.accept(this.nums[this.i])) this.i++;
    return this.i < this.nums.length;
  }

  next() {
    this.hasNext();
    return this.nums[this.i++];
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "FilterIterator" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new FilterIterator(...argumentLists[0]);
  const allowed = new Set(["hasNext", "next"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.FilterIterator = FilterIterator;
