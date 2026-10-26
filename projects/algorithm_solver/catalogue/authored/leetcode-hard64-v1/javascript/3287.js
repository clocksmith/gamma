'use strict';

// 3287. Find the Maximum Sequence Value of Array: combine exact-count OR states on both sides of every split.
// O(n*k*U + n*U^2) time and O((n+k)*U) space, U=128. Inputs are preserved.
function solve(nums, k) {
  const n = nums.length;
  const leftStates = new Array(n);
  let states = Array.from({ length: k + 1 }, () => new Set());
  states[0].add(0);
  for (let index = 0; index < n; index += 1) {
    for (let chosen = Math.min(k, index + 1); chosen > 0; chosen -= 1) {
      for (const previous of states[chosen - 1]) states[chosen].add(previous | nums[index]);
    }
    leftStates[index] = new Set(states[k]);
  }
  states = Array.from({ length: k + 1 }, () => new Set());
  states[0].add(0);
  let answer = 0;
  for (let index = n - 1; index >= 0; index -= 1) {
    for (let chosen = Math.min(k, n - index); chosen > 0; chosen -= 1) {
      for (const previous of states[chosen - 1]) states[chosen].add(previous | nums[index]);
    }
    if (index >= k && n - index >= k) {
      for (const left of leftStates[index - 1]) {
        for (const right of states[k]) answer = Math.max(answer, left ^ right);
      }
    }
  }
  return answer;
}

const maxValue = solve;
class Solution {
  maxValue(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxValue };
