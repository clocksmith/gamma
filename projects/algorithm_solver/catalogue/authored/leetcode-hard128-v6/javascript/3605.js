'use strict';

// 3605. Minimum Stability Factor of Array.
// Binary-search the longest allowed gcd-stable window and greedily replace the right endpoint of each uncovered bad window; O(n log n) gcd calls and O(n log n) space. Inputs are preserved.

function solve(nums, maxC) {
  const n = nums.length, logs = new Int32Array(n + 1);
  for (let length = 2; length <= n; length += 1) logs[length] = logs[Math.floor(length / 2)] + 1;
  function gcd(a, b) { while (b) { const remainder = a % b; a = b; b = remainder; } return a; }
  const table = [Int32Array.from(nums)];
  for (let width = 2; width <= n; width *= 2) {
    const half = width / 2, previous = table[table.length - 1], current = new Int32Array(n - width + 1);
    for (let index = 0; index < current.length; index += 1) current[index] = gcd(previous[index], previous[index + half]);
    table.push(current);
  }
  function possible(length) {
    const window = length + 1;
    if (window > n) return true;
    const level = logs[window], span = 2 ** level;
    let start = 0, changes = 0;
    while (start + window <= n) {
      if (gcd(table[level][start], table[level][start + window - span]) > 1) {
        changes += 1;
        if (changes > maxC) return false;
        start += window;
      } else start += 1;
    }
    return true;
  }
  let lower = 0, upper = n;
  while (lower < upper) {
    const middle = Math.floor((lower + upper) / 2);
    if (possible(middle)) upper = middle; else lower = middle + 1;
  }
  return lower;
}

const minStable = solve;
class Solution {
  minStable(nums, maxC) { return solve(nums, maxC); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minStable };
