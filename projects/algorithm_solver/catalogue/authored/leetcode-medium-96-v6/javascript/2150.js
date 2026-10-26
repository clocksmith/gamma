'use strict';

// 2150. Find All Lonely Numbers in the Array: retain unique values whose two neighboring integers are absent.
// O(n) expected time and O(n) auxiliary and result space; inputs are read-only.
function solve(nums) {
  const counts = new Map();
  for (const value of nums) counts.set(value, (counts.get(value) || 0) + 1);
  return nums.filter(value => counts.get(value) === 1 &&
    !counts.has(value - 1) && !counts.has(value + 1));
}

const findLonely = solve;
class Solution {
  findLonely(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLonely };
