"use strict";
// Hack2Hire 6827b84d285cf34924f48286 (Pin Board Connectivity, variant 1) over an INFERRED spec; qualification unknown.

function solve(boards, pin1, pin2) {
  const parent = new Map();
  const find = (x) => {
    while (parent.get(x) !== x) { const g = parent.get(parent.get(x)); parent.set(x, g); x = g; }
    return x;
  };
  for (const board of boards) {
    for (const pin of board) if (!parent.has(pin)) parent.set(pin, pin);
    const root = find(board[0]);
    for (let i = 1; i < board.length; i++) {
      const other = find(board[i]);
      if (other !== root) parent.set(other, root);
    }
  }
  if (!parent.has(pin1) || !parent.has(pin2)) return false;
  return find(pin1) === find(pin2);
}

function arePinsRelated(boards, pin1, pin2) { return solve(boards, pin1, pin2); }

module.exports = solve;
module.exports.arePinsRelated = arePinsRelated;
