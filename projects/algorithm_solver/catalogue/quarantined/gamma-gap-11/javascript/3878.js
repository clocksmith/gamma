'use strict';

// 3878. Count Good Subarrays.
// O(n B) expected time and O(n+B) space, B<=31; compressed suffix-OR intervals joined to the last matching element.
function solve(nums) {
  let groups = [];
  const last = new Map();
  let answer = 0;
  for (let right = 0; right < nums.length; right += 1) {
    const value = nums[right];
    last.set(value, right);
    const following = [[value, 1]];
    for (const [previous, count] of groups) {
      const combined = previous | value;
      if (following[following.length - 1][0] === combined) following[following.length - 1][1] += count;
      else following.push([combined, count]);
    }
    groups = following;
    let upper = right;
    for (const [combined, count] of groups) {
      const lower = upper - count + 1;
      const occurrence = last.has(combined) ? last.get(combined) : -1;
      answer += Math.max(0, Math.min(upper, occurrence) - lower + 1);
      upper = lower - 1;
    }
  }
  return answer;
}

const countGoodSubarrays = solve;
class Solution {
  countGoodSubarrays(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countGoodSubarrays };
