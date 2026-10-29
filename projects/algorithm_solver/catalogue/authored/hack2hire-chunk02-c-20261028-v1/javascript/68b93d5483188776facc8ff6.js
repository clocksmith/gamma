"use strict";
// Hack2Hire 68b93d5483188776facc8ff6 (Design Connect Four, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
const ROWS = 6, COLUMNS = 7;
class ConnectFour {
  constructor() {
    this.board = Array.from({length: ROWS}, () => new Array(COLUMNS).fill(null)); // row 0 is the bottom
    this.heights = new Array(COLUMNS).fill(0);
    this.turn = "A";
    this.moves = 0;
    this.over = false;
  }
  run(row, column, dRow, dColumn, player) {
    let count = 0;
    for (row += dRow, column += dColumn; row >= 0 && row < ROWS && column >= 0 && column < COLUMNS && this.board[row][column] === player; row += dRow, column += dColumn) count++;
    return count;
  }
  play(column) {
    if (this.over || !Number.isInteger(column) || column < 0 || column >= COLUMNS || this.heights[column] === ROWS) return "INVALID";
    const player = this.turn, row = this.heights[column];
    this.board[row][column] = player;
    this.heights[column]++;
    this.moves++;
    this.turn = player === "A" ? "B" : "A";
    for (const [dRow, dColumn] of [[0, 1], [1, 0], [1, 1], [1, -1]]) {
      if (1 + this.run(row, column, dRow, dColumn, player) + this.run(row, column, -dRow, -dColumn, player) >= 4) {
        this.over = true;
        return player + "_WINS";
      }
    }
    if (this.moves === ROWS * COLUMNS) { this.over = true; return "DRAW"; }
    return "ONGOING";
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ConnectFour") throw new Error("exact initial constructor required");
  const instance = new ConnectFour(...argumentLists[0]);
  const allowed = new Set(["play"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.ConnectFour = ConnectFour;
