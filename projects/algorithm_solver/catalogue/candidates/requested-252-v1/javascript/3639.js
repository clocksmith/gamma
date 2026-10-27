'use strict';

// 3639. Minimum Time to Activate String.
// Specification: https://leetcode.com/problems/minimum-time-to-activate-string/description/
// Authored candidate; not executed, syntax-checked, tested, or Gamma-qualified.
// O(n log n) time, O(n) space; valid substrings contain at least one activated position.
// Inputs are not modified.

function solve(s, order, k) {
  const size = s.length, total = size * (size + 1) / 2;
  if (k > total) return -1;
  const activation = new Int32Array(size);
  for (let time = 0; time < size; time++) activation[order[time]] = time;
  function enough(time) {
    let invalid = 0, run = 0;
    for (let index = 0; index < size; index++) {
      if (activation[index] > time) { run++; invalid += run; }
      else run = 0;
    }
    return total - invalid >= k;
  }
  let left = 0, right = size - 1;
  while (left < right) {
    const middle = Math.floor((left + right) / 2);
    if (enough(middle)) right = middle;
    else left = middle + 1;
  }
  return left;
}

const minTime = solve;
class Solution {
  minTime(s, order, k) { return solve(s, order, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minTime };
