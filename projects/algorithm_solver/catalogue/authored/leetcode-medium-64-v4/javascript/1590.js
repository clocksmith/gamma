'use strict';

// 1590. Make Sum Divisible by P: match prefix remainders using the latest index for the shortest removable interval.
// O(n) expected time and O(min(n, p)) auxiliary space; inputs are read-only.
function solve(nums, p) {
  let required = 0;
  for (const value of nums) required = (required + value) % p;
  if (required === 0) return 0;
  const latest = new Map([[0, -1]]);
  let prefix = 0;
  let best = nums.length;
  for (let index = 0; index < nums.length; index += 1) {
    prefix = (prefix + nums[index]) % p;
    const wanted = (prefix - required + p) % p;
    if (latest.has(wanted)) best = Math.min(best, index - latest.get(wanted));
    latest.set(prefix, index);
  }
  return best < nums.length ? best : -1;
}

const minSubarray = solve;
class Solution {
  minSubarray(nums, p) { return solve(nums, p); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minSubarray };
