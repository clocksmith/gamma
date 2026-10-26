'use strict';

// 3399. Smallest Substring With Identical Characters II: special-case alternation then binary search the longest allowed run.
// O(n log n) time and O(n) auxiliary space. Inputs are preserved.
function solve(s, numOps) {
  const n = s.length;
  let mismatches = 0;
  for (let index = 0; index < n; index += 1) {
    if (s.charCodeAt(index) - 48 !== index % 2) mismatches += 1;
  }
  if (Math.min(mismatches, n - mismatches) <= numOps) return 1;
  const runs = [];
  let length = 0;
  let previous = '';
  let maximum = 0;
  for (const character of s) {
    if (character === previous) {
      length += 1;
    } else {
      if (length > 0) {
        runs.push(length);
        maximum = Math.max(maximum, length);
      }
      length = 1;
      previous = character;
    }
  }
  runs.push(length);
  maximum = Math.max(maximum, length);
  let left = 2;
  let right = maximum;
  while (left < right) {
    const middle = Math.floor((left + right) / 2);
    let required = 0;
    for (const run of runs) required += Math.floor(run / (middle + 1));
    if (required <= numOps) right = middle;
    else left = middle + 1;
  }
  return left;
}

const minLength = solve;
class Solution {
  minLength(s, numOps) { return solve(s, numOps); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minLength };
