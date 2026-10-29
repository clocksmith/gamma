"use strict";
// Hack2Hire 69dd348b95e80ae213e5b702 (Design Connect Four II, variant 2 of 2) over an INFERRED spec; qualification unknown.

class ConnectFourBoard {
  constructor(rows, cols) {
    this.rows = rows;
    this.cols = cols;
    this.grid = [];
    for (let r = 0; r < rows; r++) this.grid.push(new Array(cols).fill("0"));
    this.height = new Array(cols).fill(0);
    this.winner = "0";
  }

  run(r, c, dr, dc, color) {
    let length = 0;
    r += dr; c += dc;
    while (r >= 0 && r < this.rows && c >= 0 && c < this.cols && this.grid[r][c] === color) { length++; r += dr; c += dc; }
    return length;
  }

  drop(color, col) {
    if (this.height[col] < this.rows) {
      const r = this.rows - 1 - this.height[col];
      this.grid[r][col] = color;
      this.height[col] += 1;
      if (this.winner === "0") {
        for (const [dr, dc] of [[0, 1], [1, 0], [1, 1], [1, -1]]) {
          if (1 + this.run(r, col, dr, dc, color) + this.run(r, col, -dr, -dc, color) >= 4) { this.winner = color; break; }
        }
      }
    }
    return this.grid.map((row) => row.slice());
  }

  getWinner() {
    return this.winner;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ConnectFourBoard" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new ConnectFourBoard(...argumentLists[0]);
  const allowed = new Set(["drop", "getWinner"]);
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
