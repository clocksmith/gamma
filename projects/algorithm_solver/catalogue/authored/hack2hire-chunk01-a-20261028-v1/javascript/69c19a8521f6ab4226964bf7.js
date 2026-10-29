"use strict";
// Hack2Hire 69c19a8521f6ab4226964bf7 (Design Connect K Board) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
class ConnectKGame {
  constructor(k) {
    this.k = k;
    this.columns = new Map(); // column -> array whose last element is height 0 (bottom insertion is a push)
  }
  cell(column, height) {
    const pieces = this.columns.get(column);
    if (pieces === undefined || height < 0 || height >= pieces.length) return null;
    return pieces[pieces.length - 1 - height];
  }
  placePiece(player, column) {
    if (!this.columns.has(column)) this.columns.set(column, []);
    const pieces = this.columns.get(column), k = this.k;
    pieces.push(player);
    const height = pieces.length;
    let run = 0;
    for (const value of pieces) { // vertical runs live entirely inside this column
      run = value === player ? run + 1 : 0;
      if (run >= k) return true;
    }
    for (let y = 0; y < height; y++) {
      if (pieces[height - 1 - y] !== player) continue;
      for (const [dx, dy] of [[1, 0], [1, 1], [1, -1]]) {
        let count = 1;
        for (const sign of [1, -1]) {
          for (let step = 1; count < k && this.cell(column + sign * dx * step, y + sign * dy * step) === player; step++) count++;
        }
        if (count >= k) return true;
      }
    }
    return false;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "ConnectKGame" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new ConnectKGame(...argumentLists[0]), allowed = new Set(["placePiece"]), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.ConnectKGame = ConnectKGame;
