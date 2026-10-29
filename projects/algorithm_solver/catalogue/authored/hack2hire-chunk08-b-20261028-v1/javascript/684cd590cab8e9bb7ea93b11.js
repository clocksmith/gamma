"use strict";
// Hack2Hire 684cd590cab8e9bb7ea93b11 (Tic-Tac-Toe II) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.

const DIRECTIONS = [[0, 1], [1, 0], [1, 1], [1, -1]];

class TicTacToe {
  constructor(n, m, k) {
    this.m = m; this.k = k;
    this.owner = new Map();
    this.run = [new Map(), new Map(), new Map(), new Map()];   // per direction: run length stored at both endpoints
  }

  move(row, col, player) {
    const m = this.m, owner = this.owner, cell = row * m + col;
    owner.set(cell, player);
    let won = false;
    for (let d = 0; d < 4; d++) {
      const [dr, dc] = DIRECTIONS[d], run = this.run[d], step = dr * m + dc;
      const left = col - dc >= 0 && col - dc < m && owner.get(cell - step) === player ? run.get(cell - step) : 0;
      const right = col + dc >= 0 && col + dc < m && owner.get(cell + step) === player ? run.get(cell + step) : 0;
      const total = left + right + 1;
      run.set(cell - left * step, total);
      run.set(cell + right * step, total);
      if (total >= this.k) won = true;
    }
    return won ? player : 0;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "TicTacToe" || argumentLists[0].length !== 3) throw new Error("exact initial constructor required");
  const instance = new TicTacToe(...argumentLists[0]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (operationNames[i] !== "move") throw new Error("unknown method");
    result.push(instance.move(...argumentLists[i]));
  }
  return result;
}

module.exports = solve;
module.exports.TicTacToe = TicTacToe;
