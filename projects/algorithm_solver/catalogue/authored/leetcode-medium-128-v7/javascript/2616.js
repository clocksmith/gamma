'use strict';

// 2616. Minimize the Maximum Difference of Pairs: binary search the permitted gap and greedily pair adjacent sorted values.
// O(n log n + n log(M + 1)) time and O(n) auxiliary space, where M is the value range; inputs are read-only.
function solve(nums, p) {
  if (p === 0) return 0;
  const ordered = nums.slice().sort((left, right) => left - right);
  let low = 0;
  let high = ordered[ordered.length - 1] - ordered[0];
  while (low < high) {
    const bound = Math.floor((low + high) / 2);
    let pairs = 0;
    let index = 1;
    while (index < ordered.length) {
      if (ordered[index] - ordered[index - 1] <= bound) {
        pairs += 1;
        index += 2;
      } else index += 1;
    }
    if (pairs >= p) high = bound;
    else low = bound + 1;
  }
  return low;
}

const minimizeMax = solve;
class Solution {
  minimizeMax(nums, p) { return solve(nums, p); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimizeMax };
