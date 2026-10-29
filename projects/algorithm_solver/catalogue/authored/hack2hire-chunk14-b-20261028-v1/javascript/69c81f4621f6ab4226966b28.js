"use strict";
// Hack2Hire 69c81f4621f6ab4226966b28 (Winner in a Dot Grid Game) over an INFERRED spec; qualification unknown.

function solve(moves) {
  const horizontal = Array.from({length: 9}, () => new Array(8).fill(false));
  const vertical = Array.from({length: 8}, () => new Array(9).fill(false));
  const closed = (r, c) => horizontal[r][c] && horizontal[r + 1][c] && vertical[r][c] && vertical[r][c + 1];
  const score = [0, 0];
  moves.forEach(([r1, c1, r2, c2], k) => {
    const r = Math.min(r1, r2), c = Math.min(c1, c2);
    let gained = 0;
    if (r1 === r2) {
      horizontal[r][c] = true;
      if (r >= 1 && closed(r - 1, c)) gained++;
      if (r <= 7 && closed(r, c)) gained++;
    } else {
      vertical[r][c] = true;
      if (c >= 1 && closed(r, c - 1)) gained++;
      if (c <= 7 && closed(r, c)) gained++;
    }
    score[k % 2] += gained;
  });
  if (score[0] === score[1]) return 0;
  return score[0] > score[1] ? 1 : 2;
}

function dotGridWinner(moves) { return solve(moves); }

module.exports = solve;
module.exports.dotGridWinner = dotGridWinner;
