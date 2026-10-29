"use strict";
// Hack2Hire 69bdbad91cbff60a929beb23 (Design Connect Four II, variant 1 of 2) over an INFERRED spec; qualification unknown.

class ConnectFourBoard {
  constructor(rows, cols) {
    this.rows = rows;
    this.grid = [];
    for (let r = 0; r < rows; r++) this.grid.push(new Array(cols).fill("0"));
    this.height = new Array(cols).fill(0);
  }

  drop(color, col) {
    if (this.height[col] < this.rows) {
      this.grid[this.rows - 1 - this.height[col]][col] = color;
      this.height[col] += 1;
    }
    return this.grid.map((row) => row.slice());
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ConnectFourBoard" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new ConnectFourBoard(...argumentLists[0]);
  const allowed = new Set(["drop"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.ConnectFourBoard = ConnectFourBoard;
