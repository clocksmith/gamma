'use strict';

// 1589. Maximum Sum Obtained of Any Permutation: pair the largest values with the most-requested positions using a difference array.
// O(n log(n + 1) + q) time and O(n) auxiliary space; inputs are read-only.
function solve(nums, requests) {
  const modulus = 1000000007;
  const difference = new Int32Array(nums.length + 1);
  for (const [left, right] of requests) {
    difference[left] += 1;
    difference[right + 1] -= 1;
  }
  const frequencies = [];
  let active = 0;
  for (let index = 0; index < nums.length; index += 1) {
    active += difference[index];
    frequencies.push(active);
  }
  frequencies.sort((a, b) => a - b);
  const ordered = nums.slice().sort((a, b) => a - b);
  let total = 0;
  for (let index = 0; index < nums.length; index += 1) {
    total = (total + ordered[index] * frequencies[index]) % modulus;
  }
  return total;
}

const maxSumRangeQuery = solve;
class Solution {
  maxSumRangeQuery(nums, requests) { return solve(nums, requests); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSumRangeQuery };
