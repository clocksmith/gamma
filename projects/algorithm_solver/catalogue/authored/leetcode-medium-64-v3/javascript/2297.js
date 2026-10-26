'use strict';

// 2297. Jump Game VIII: relax the next greater-or-equal and next smaller jumps with two monotone stacks.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums, costs) {
  const distance = new Array(nums.length).fill(Infinity);
  distance[0] = 0;
  const decreasing = [];
  const increasing = [];
  for (let index = 0; index < nums.length; index += 1) {
    while (decreasing.length && nums[decreasing[decreasing.length - 1]] <= nums[index]) {
      const previous = decreasing.pop();
      distance[index] = Math.min(distance[index], distance[previous] + costs[index]);
    }
    while (increasing.length && nums[increasing[increasing.length - 1]] > nums[index]) {
      const previous = increasing.pop();
      distance[index] = Math.min(distance[index], distance[previous] + costs[index]);
    }
    decreasing.push(index);
    increasing.push(index);
  }
  return distance[distance.length - 1];
}

const minCost = solve;
class Solution {
  minCost(nums, costs) { return solve(nums, costs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCost };
