'use strict';

// 2615. Sum of Distances: accumulate equal-value index distances in forward and backward passes.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const answer = new Array(nums.length).fill(0);
  const counts = new Map();
  const totals = new Map();
  for (let index = 0; index < nums.length; index += 1) {
    const value = nums[index];
    const count = counts.get(value) || 0;
    const total = totals.get(value) || 0;
    answer[index] += index * count - total;
    counts.set(value, count + 1);
    totals.set(value, total + index);
  }
  counts.clear();
  totals.clear();
  for (let index = nums.length - 1; index >= 0; index -= 1) {
    const value = nums[index];
    const count = counts.get(value) || 0;
    const total = totals.get(value) || 0;
    answer[index] += total - index * count;
    counts.set(value, count + 1);
    totals.set(value, total + index);
  }
  return answer;
}

const distance = solve;
class Solution {
  distance(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, distance };
