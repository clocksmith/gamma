'use strict';

// 3854. Minimum Operations to Make Array Parity Alternating.
// O(n log n) time and O(n) space; minimum-flip parity patterns followed by a smallest covering range of legal values.
function solve(nums) {
  const n = nums.length;
  const costs = [0, 0];
  for (let first = 0; first < 2; first += 1) {
    for (let index = 0; index < n; index += 1) if ((nums[index] & 1) !== ((index + first) & 1)) costs[first] += 1;
  }
  const minimum = Math.min(...costs);
  let bestRange = Infinity;
  for (let first = 0; first < 2; first += 1) {
    if (costs[first] !== minimum) continue;
    const options = [];
    for (let index = 0; index < n; index += 1) {
      if ((nums[index] & 1) === ((index + first) & 1)) options.push([nums[index], index]);
      else {
        options.push([nums[index] - 1, index]);
        options.push([nums[index] + 1, index]);
      }
    }
    options.sort((left, right) => left[0] - right[0]);
    const counts = Array(n).fill(0);
    let covered = 0;
    let left = 0;
    for (const [value, index] of options) {
      if (counts[index] === 0) covered += 1;
      counts[index] += 1;
      while (covered === n) {
        bestRange = Math.min(bestRange, value - options[left][0]);
        const dropped = options[left][1];
        counts[dropped] -= 1;
        if (counts[dropped] === 0) covered -= 1;
        left += 1;
      }
    }
  }
  return [minimum, bestRange];
}

const makeParityAlternating = solve;
class Solution {
  makeParityAlternating(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, makeParityAlternating };
