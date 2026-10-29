"use strict";
// Hack2Hire 68539b6bd3dbd4fb8b026e9f (Design Lazy Array) over an INFERRED spec; qualification unknown.

class LazyArray {
  constructor(arr) {
    this.size = arr.length;
    this.first = new Map();
    for (let i = 0; i < arr.length; i++) if (!this.first.has(arr[i])) this.first.set(arr[i], i);
    this.a = 1;
    this.b = 0;
  }

  map(operation, operand) {
    if (operation === "add") {
      this.b += operand;
    } else {
      this.a *= operand;
      this.b *= operand;
    }
  }

  indexOf(target) {
    if (this.a === 0) return this.size > 0 && this.b === target ? 0 : -1;
    const diff = target - this.b;
    if (diff % this.a !== 0) return -1;
    const x = diff / this.a;
    const index = this.first.get(x);
    return index === undefined ? -1 : index;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "LazyArray" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new LazyArray(...argumentLists[0]);
  const allowed = new Set(["map", "indexOf"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.LazyArray = LazyArray;
