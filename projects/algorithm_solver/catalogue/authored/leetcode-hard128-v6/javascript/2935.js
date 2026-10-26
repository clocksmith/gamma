'use strict';

// 2935. Maximum Strong Pair XOR II.
// Sorted sliding window and a counted binary trie; O(n log n + n*B) time, O(n*B) space. Inputs are preserved.

function solve(nums) {
  const values = nums.slice().sort((a, b) => a - b);
  const bits = Math.max(1, Math.floor(Math.log2(values[values.length - 1])) + 1), children = [[-1, -1]], counts = [0];
  function update(value, change) {
    let state = 0; counts[state] += change;
    for (let bit = bits - 1; bit >= 0; bit -= 1) {
      const digit = (value >>> bit) & 1;
      if (children[state][digit] === -1) { children[state][digit] = children.length; children.push([-1, -1]); counts.push(0); }
      state = children[state][digit]; counts[state] += change;
    }
  }
  let left = 0, answer = 0;
  for (const value of values) {
    update(value, 1);
    while (value > 2 * values[left]) { update(values[left], -1); left += 1; }
    let state = 0, score = 0;
    for (let bit = bits - 1; bit >= 0; bit -= 1) {
      const digit = (value >>> bit) & 1, opposite = children[state][digit ^ 1];
      if (opposite !== -1 && counts[opposite] > 0) { score += 2 ** bit; state = opposite; }
      else state = children[state][digit];
    }
    answer = Math.max(answer, score);
  }
  return answer;
}

const maximumStrongPairXor = solve;
class Solution {
  maximumStrongPairXor(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumStrongPairXor };
