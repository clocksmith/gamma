'use strict';

// 1524. Number of Sub-arrays With Odd Sum: count earlier prefix sums whose parity differs from the current prefix.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(arr) {
  const modulus = 1000000007;
  const counts = [1, 0];
  let parity = 0;
  let total = 0;
  for (const value of arr) {
    parity = (parity + value) % 2;
    total = (total + counts[1 - parity]) % modulus;
    counts[parity] += 1;
  }
  return total;
}

const numOfSubarrays = solve;
class Solution {
  numOfSubarrays(arr) { return solve(arr); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numOfSubarrays };
