"use strict";

function solve(stream, pattern) {
  const m = pattern.length;
  const pi = new Int32Array(m);
  let j = 0;
  for (let i = 1; i < m; i++) {
    while (j > 0 && pattern[i] !== pattern[j]) j = pi[j - 1];
    if (pattern[i] === pattern[j]) j++;
    pi[i] = j;
  }
  const isArr = Array.isArray(stream);
  const limit = isArr ? stream.length : 10000000;
  j = 0;
  for (let idx = 0; idx < limit; idx++) {
    const b = isArr ? stream[idx] : stream.next();
    while (j > 0 && b !== pattern[j]) j = pi[j - 1];
    if (b === pattern[j]) {
      j++;
      if (j === m) return idx - m + 1;
    }
  }
  return -1;
}

function findPattern(stream, pattern) {
  return solve(stream, pattern);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.findPattern = findPattern;
