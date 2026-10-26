'use strict';

// 1638. Count Substrings That Differ by One Character: extend equal and one-mismatch suffix counts along matching diagonals.
// O(n * m) time and O(m) auxiliary space; inputs are read-only.
function solve(s, t) {
  const equal = new Int32Array(t.length + 1);
  const different = new Int32Array(t.length + 1);
  let total = 0;
  for (const first of s) {
    let previousEqual = 0;
    let previousDifferent = 0;
    for (let index = 1; index <= t.length; index += 1) {
      const oldEqual = equal[index];
      const oldDifferent = different[index];
      if (first === t[index - 1]) {
        equal[index] = previousEqual + 1;
        different[index] = previousDifferent;
      } else {
        equal[index] = 0;
        different[index] = previousEqual + 1;
      }
      total += different[index];
      previousEqual = oldEqual;
      previousDifferent = oldDifferent;
    }
  }
  return total;
}

const countSubstrings = solve;
class Solution {
  countSubstrings(s, t) { return solve(s, t); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countSubstrings };
