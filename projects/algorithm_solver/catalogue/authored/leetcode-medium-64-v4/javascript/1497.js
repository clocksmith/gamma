'use strict';

// 1497. Check If Array Pairs Are Divisible by k: match complementary normalized remainder counts.
// O(n + k) time and O(k) auxiliary space; inputs are read-only.
function solve(arr, k) {
  const counts = new Int32Array(k);
  for (const value of arr) counts[((value % k) + k) % k] += 1;
  if (counts[0] % 2 !== 0) return false;
  for (let remainder = 1; remainder < Math.ceil(k / 2); remainder += 1) {
    if (counts[remainder] !== counts[k - remainder]) return false;
  }
  return k % 2 === 1 || counts[k / 2] % 2 === 0;
}

const canArrange = solve;
class Solution {
  canArrange(arr, k) { return solve(arr, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canArrange };
