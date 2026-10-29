"use strict";

function solve(currentState) {
  const runs = [];
  let cur = 0;
  for (let i = 0; i < currentState.length; i++) {
    if (currentState[i] === "+") {
      cur++;
    } else {
      if (cur >= 2) runs.push(cur);
      cur = 0;
    }
  }
  if (cur >= 2) runs.push(cur);
  if (runs.length === 0) return false;
  let mx = 0;
  for (let i = 0; i < runs.length; i++) if (runs[i] > mx) mx = runs[i];
  const g = new Int32Array(mx + 1);
  for (let L = 2; L <= mx; L++) {
    const seen = new Set();
    for (let i = 0; i <= (L - 1) >> 1; i++) {
      seen.add(g[i] ^ g[L - 2 - i]);
    }
    let mex = 0;
    while (seen.has(mex)) mex++;
    g[L] = mex;
  }
  let xorSum = 0;
  for (let i = 0; i < runs.length; i++) xorSum ^= g[runs[i]];
  return xorSum !== 0;
}

function canWin(currentState) {
  return solve(currentState);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.canWin = canWin;
