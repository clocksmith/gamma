'use strict';

// 2808. Minimum Seconds to Equalize a Circular Array (Medium).
// Specification: https://leetcode.com/problems/minimum-seconds-to-equalize-a-circular-array/description/
function solve(nums) {
  const n = nums.length;
  const positions = new Map();
  for (let i = 0; i < n; i++) {
    if (!positions.has(nums[i])) positions.set(nums[i], []);
    positions.get(nums[i]).push(i);
  }
  let ans = n;
  for (const pos of positions.values()) {
    let maxGap = 0;
    for (let j = 0; j < pos.length; j++) {
      const cur = pos[j];
      const nxt = j + 1 < pos.length ? pos[j + 1] : pos[0] + n;
      maxGap = Math.max(maxGap, nxt - cur);
    }
    ans = Math.min(ans, Math.floor(maxGap / 2));
  }
  return ans;
}
const minimumSeconds = solve;
class Solution {
  minimumSeconds(...args) { return solve(...args); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumSeconds };
