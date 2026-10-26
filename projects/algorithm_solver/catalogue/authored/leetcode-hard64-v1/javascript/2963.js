'use strict';

// 2963. Count the Number of Good Partitions: merge value-occurrence intervals and choose independent boundaries.
// O(n) expected time and O(n) auxiliary space. Inputs are preserved.
function solve(nums) {
  const last = new Map();
  for (let index = 0; index < nums.length; index += 1) last.set(nums[index], index);
  let end = 0;
  let answer = 1;
  for (let index = 0; index < nums.length; index += 1) {
    end = Math.max(end, last.get(nums[index]));
    if (index === end && index + 1 < nums.length) answer = answer * 2 % 1000000007;
  }
  return answer;
}

const numberOfGoodPartitions = solve;
class Solution {
  numberOfGoodPartitions(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, numberOfGoodPartitions };
