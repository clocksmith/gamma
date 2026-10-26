'use strict';

// 2293. Min Max Game (Easy).
// Specification: https://leetcode.com/problems/min-max-game/description/
// O(n) time, O(n) space; reduce alternating min/max pairs on copies; preserve nums.
function solve(nums) {
  let current = nums.slice();
  while (current.length > 1) {
    const next = new Array(current.length / 2);
    for (let index = 0; index < next.length; index++) {
      const first = current[index * 2];
      const second = current[index * 2 + 1];
      next[index] = index % 2 === 0 ? Math.min(first, second) : Math.max(first, second);
    }
    current = next;
  }
  return current[0];
}

const minMaxGame = solve;
class Solution {
  minMaxGame(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMaxGame };
