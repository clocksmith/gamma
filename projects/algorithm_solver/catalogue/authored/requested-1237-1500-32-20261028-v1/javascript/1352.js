"use strict";

class ProductOfNumbers {
  constructor() {
    this.prefix = [1];
  }
  add(num) {
    if (num === 0) {
      this.prefix = [1];
    } else {
      this.prefix.push(this.prefix[this.prefix.length - 1] * num);
    }
  }
  getProduct(k) {
    if (k >= this.prefix.length) return 0;
    return Math.round(this.prefix[this.prefix.length - 1] / this.prefix[this.prefix.length - 1 - k]);
  }
}

function solve(operation_names, argument_lists) {
  const inst = new ProductOfNumbers();
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i], args = argument_lists[i];
    if (op === "add") { inst.add(args[0]); out.push(null); }
    else out.push(inst.getProduct(args[0]));
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.ProductOfNumbers = ProductOfNumbers;
