'use strict';

// 2910. Minimum Number of Groups to Create a Valid Assignment: try descending base group sizes and express each frequency using adjacent sizes.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const counts = new Map();
  for (const value of nums) counts.set(value, (counts.get(value) || 0) + 1);
  const frequencies = Array.from(counts.values());
  let minimum = nums.length;
  for (const frequency of frequencies) minimum = Math.min(minimum, frequency);
  for (let small = minimum; small >= 1; small -= 1) {
    let total = 0;
    let feasible = true;
    for (const frequency of frequencies) {
      const groups = Math.ceil(frequency / (small + 1));
      if (groups * small > frequency) {
        feasible = false;
        break;
      }
      total += groups;
    }
    if (feasible) return total;
  }
  return nums.length;
}

const minGroupsForValidAssignment = solve;
class Solution {
  minGroupsForValidAssignment(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minGroupsForValidAssignment };
