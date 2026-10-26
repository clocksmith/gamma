'use strict';

// 3811. Number of Alternating XOR Partitions.
// O(n) expected time and O(n) space; snapshots both transitions before adding the current prefix.
function solve(nums, target1, target2) {
  const modulus = 1000000007;
  const even = new Map([[0, 1]]);
  const odd = new Map();
  let prefix = 0;
  let lastEven = 0;
  let lastOdd = 0;
  for (const value of nums) {
    prefix ^= value;
    lastOdd = even.get(prefix ^ target1) || 0;
    lastEven = odd.get(prefix ^ target2) || 0;
    odd.set(prefix, ((odd.get(prefix) || 0) + lastOdd) % modulus);
    even.set(prefix, ((even.get(prefix) || 0) + lastEven) % modulus);
  }
  return (lastEven + lastOdd) % modulus;
}

const countPartitions = solve;
class Solution {
  countPartitions(nums, target1, target2) { return solve(nums, target1, target2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPartitions };
