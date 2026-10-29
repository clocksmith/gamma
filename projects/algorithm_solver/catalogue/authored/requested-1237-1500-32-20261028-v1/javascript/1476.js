"use strict";

class SubrectangleQueries {
  constructor(rectangle) {
    this.base = rectangle.map((r) => r.slice());
    this.ops = [];
  }
  updateSubrectangle(row1, col1, row2, col2, newValue) {
    this.ops.push([row1, col1, row2, col2, newValue]);
  }
  getValue(row, col) {
    for (let i = this.ops.length - 1; i >= 0; i--) {
      const [r1, c1, r2, c2, v] = this.ops[i];
      if (row >= r1 && row <= r2 && col >= c1 && col <= c2) return v;
    }
    return this.base[row][col];
  }
}

function solve(operation_names, argument_lists) {
  const inst = new SubrectangleQueries(argument_lists[0][0]);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i], args = argument_lists[i];
    if (op === "updateSubrectangle") {
      inst.updateSubrectangle(args[0], args[1], args[2], args[3], args[4]);
      out.push(null);
    } else {
      out.push(inst.getValue(args[0], args[1]));
    }
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.SubrectangleQueries = SubrectangleQueries;
