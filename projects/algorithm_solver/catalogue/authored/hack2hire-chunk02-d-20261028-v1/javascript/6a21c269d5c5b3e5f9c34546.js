"use strict";
// Hack2Hire 6a21c269d5c5b3e5f9c34546 (Find Valid Tile Moves) over an INFERRED spec; qualification unknown.

function solve(start, target) {
  if (start.slice().sort().join("") !== target.slice().sort().join("")) return false;
  const goal = target.join(""), first = start.join(""), n = first.length;
  const seen = new Set([first]);
  const stack = [first];
  while (stack.length) {
    const board = stack.pop();
    if (board === goal) return true;
    for (let i = 0; i < n; i++) {
      let next = null;
      if (board[i] === "R") {
        if (i + 1 < n && board[i + 1] === "_") next = board.slice(0, i) + "_R" + board.slice(i + 2);
        else if (i + 2 < n && board[i + 1] === "B" && board[i + 2] === "_") next = board.slice(0, i) + "_BR" + board.slice(i + 3);
      } else if (board[i] === "B") {
        if (i >= 1 && board[i - 1] === "_") next = board.slice(0, i - 1) + "B_" + board.slice(i + 1);
        else if (i >= 2 && board[i - 1] === "R" && board[i - 2] === "_") next = board.slice(0, i - 2) + "BR_" + board.slice(i + 1);
      }
      if (next !== null && !seen.has(next)) { seen.add(next); stack.push(next); }
    }
  }
  return false;
}

function canReach(start, target) { return solve(start, target); }

module.exports = solve;
module.exports.canReach = canReach;
