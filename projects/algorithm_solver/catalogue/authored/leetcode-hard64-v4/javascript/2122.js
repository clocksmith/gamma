'use strict';

// 2122. Recover the Original Array. Enumerate positive even offsets and greedily pair multiplicities; O(n^2) time and O(n) space. Inputs are preserved.

function solve(nums) {
  const ordered = nums.slice().sort((a, b) => a - b);
  const original = new Map();
  for (const value of ordered) original.set(value, (original.get(value) || 0) + 1);
  const tried = new Set();
  for (let index = 1; index < ordered.length; index += 1) {
    const difference = ordered[index] - ordered[0];
    if (difference <= 0 || difference % 2 !== 0 || tried.has(difference)) continue;
    tried.add(difference);
    const remaining = new Map(original);
    const answer = [];
    let valid = true;
    for (const lower of ordered) {
      if (remaining.get(lower) === 0) continue;
      const upper = lower + difference;
      if (!remaining.get(upper)) {
        valid = false;
        break;
      }
      remaining.set(lower, remaining.get(lower) - 1);
      remaining.set(upper, remaining.get(upper) - 1);
      answer.push(lower + difference / 2);
    }
    if (valid) return answer;
  }
  return [];
}

const recoverArray = solve;
class Solution {
  recoverArray(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, recoverArray };
