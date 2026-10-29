"use strict";

class Solution {
  constructor(radius, x_center, y_center) {
    this.radius = Number(radius);
    this.xc = Number(x_center);
    this.yc = Number(y_center);
    this._state = 0x9e3779b9 >>> 0;
  }
  _random() {
    this._state = (Math.imul(this._state, 1664525) + 1013904223) >>> 0;
    return this._state / 4294967296.0;
  }
  randPoint() {
    while (true) {
      const dx = 2.0 * this._random() - 1.0;
      const dy = 2.0 * this._random() - 1.0;
      if (dx * dx + dy * dy <= 1.0) {
        return [this.xc + this.radius * dx, this.yc + this.radius * dy];
      }
    }
  }
}

function solve(operation_names, argument_lists) {
  const [r, xc, yc] = argument_lists[0];
  const instance = new Solution(r, xc, yc);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i];
    if (op === "randPoint") out.push(instance.randPoint());
    else throw new Error("unknown operation");
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.Solution = Solution;
