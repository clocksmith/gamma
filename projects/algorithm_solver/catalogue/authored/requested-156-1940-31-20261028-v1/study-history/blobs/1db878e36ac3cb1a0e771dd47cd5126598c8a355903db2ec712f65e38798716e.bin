"use strict";

function solve(s) {
  let twos = 0;
  let i = 0;
  const n = s.length;
  while (i < n) {
    let j = i;
    while (j < n && s[j] === s[i]) j++;
    const rem = (j - i) % 3;
    if (rem === 1) return false;
    if (rem === 2) twos++;
    i = j;
  }
  return twos === 1;
}

function isDecomposable(s) {
  return solve(s);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.isDecomposable = isDecomposable;
