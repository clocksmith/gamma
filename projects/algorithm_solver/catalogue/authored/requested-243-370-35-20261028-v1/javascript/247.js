"use strict";

const PAIRS = [["0", "0"], ["1", "1"], ["6", "9"], ["8", "8"], ["9", "6"]];

function solve(n) {
  function build(rem, total) {
    if (rem === 0) return [""];
    if (rem === 1) return ["0", "1", "8"];
    const mids = build(rem - 2, total);
    const res = [];
    for (let i = 0; i < mids.length; i++) {
      const s = mids[i];
      for (let j = 0; j < PAIRS.length; j++) {
        const [a, b] = PAIRS[j];
        if (rem === total && a === "0") continue;
        res.push(a + s + b);
      }
    }
    res.sort();
    return res;
  }
  return build(n, n);
}

function findStrobogrammatic(n) {
  return solve(n);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.findStrobogrammatic = findStrobogrammatic;
