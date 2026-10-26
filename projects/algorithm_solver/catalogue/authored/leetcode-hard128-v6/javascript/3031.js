'use strict';

// 3031. Minimum Time to Revert Word to Initial State II.
// Z-function checks every possible retained suffix; O(n) time and space.

function solve(word, k) {
  const n = word.length, z = Array(n).fill(0);
  let left = 0, right = 0;
  for (let index = 1; index < n; index += 1) {
    if (index <= right) z[index] = Math.min(right - index + 1, z[index - left]);
    while (index + z[index] < n && word[z[index]] === word[index + z[index]]) z[index] += 1;
    if (index + z[index] - 1 > right) { left = index; right = index + z[index] - 1; }
  }
  for (let removed = k; removed < n; removed += k) if (z[removed] >= n - removed) return removed / k;
  return Math.ceil(n / k);
}

const minimumTimeToInitialState = solve;
class Solution {
  minimumTimeToInitialState(word, k) { return solve(word, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumTimeToInitialState };
