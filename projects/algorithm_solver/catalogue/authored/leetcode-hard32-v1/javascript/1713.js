'use strict';

// 1713. Minimum Operations to Make a Subsequence.
// O(n + m*log(n+1)) time, O(n) space. Strict LIS prevents duplicate target positions.
function solve(target, arr) {
  const positions = new Map();
  for (let index = 0; index < target.length; index += 1) positions.set(target[index], index);
  const tails = [];
  for (const value of arr) {
    if (!positions.has(value)) continue;
    const position = positions.get(value);
    let low = 0;
    let high = tails.length;
    while (low < high) {
      const middle = Math.floor((low + high) / 2);
      if (tails[middle] < position) low = middle + 1;
      else high = middle;
    }
    if (low === tails.length) tails.push(position);
    else tails[low] = position;
  }
  return target.length - tails.length;
}

const minOperations = solve;
class Solution {
  minOperations(target, arr) { return solve(target, arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
