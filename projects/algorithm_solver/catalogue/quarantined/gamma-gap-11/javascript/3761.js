'use strict';

// 3761. Minimum Absolute Distance Between Mirror Pairs.
// O(n log M) time and O(n) space; reversal is directional and lookup precedes insertion.
function solve(nums) {
  const latest = new Map();
  let answer = nums.length + 1;
  for (let index = 0; index < nums.length; index += 1) {
    const value = nums[index];
    if (latest.has(value)) answer = Math.min(answer, index - latest.get(value));
    let reversedValue = 0;
    let remaining = value;
    while (remaining > 0) {
      reversedValue = reversedValue * 10 + remaining % 10;
      remaining = Math.floor(remaining / 10);
    }
    latest.set(reversedValue, index);
  }
  return answer > nums.length ? -1 : answer;
}

const minMirrorPairDistance = solve;
class Solution {
  minMirrorPairDistance(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minMirrorPairDistance };
