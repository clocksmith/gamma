'use strict';

// 2997. Minimum Number of Operations to Make Array XOR Equal to K: count the differing bits between the array xor and the target.
// O(n + log(M + 1)) time and O(1) auxiliary space on the bounded integer domain; inputs are read-only.
function solve(nums, k) {
  let difference = k;
  for (const value of nums) difference ^= value;
  let operations = 0;
  while (difference !== 0) {
    difference &= difference - 1;
    operations += 1;
  }
  return operations;
}

const minOperations = solve;
class Solution {
  minOperations(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minOperations };
