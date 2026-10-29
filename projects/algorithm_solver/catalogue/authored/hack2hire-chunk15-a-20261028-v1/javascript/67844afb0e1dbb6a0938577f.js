"use strict";
// Hack2Hire 67844afb0e1dbb6a0938577f (Count Valid Binary Combinations) over an INFERRED spec; qualification unknown.

function solve(arr, pattern) {
  const n = pattern.length, m = arr.length;
  const zeros = new Array(n + 1).fill(0);
  for (let i = 0; i < n; i++) zeros[i + 1] = zeros[i] + (pattern[i] === "0" ? 1 : 0);
  const ways = [];
  for (let i = 0; i <= n; i++) ways.push(new Array(m + 1).fill(0));
  ways[n][m] = 1;
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m; j >= 0; j--) {
      let total = 0;
      if (pattern[i] !== "1") total += ways[i + 1][j];
      if (j < m) {
        const end = i + arr[j];
        if (end <= n && zeros[end] === zeros[i]) {
          if (end === n) total += ways[n][j + 1];
          else if (pattern[end] !== "1") total += ways[end + 1][j + 1];
        }
      }
      ways[i][j] = total;
    }
  }
  return ways[0][0];
}

function countCombinations(arr, pattern) { return solve(arr, pattern); }

module.exports = solve;
module.exports.countCombinations = countCombinations;
