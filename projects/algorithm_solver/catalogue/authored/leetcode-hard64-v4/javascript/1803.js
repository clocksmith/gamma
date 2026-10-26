'use strict';

// 1803. Count Pairs With XOR in a Range. Count prior XORs below each endpoint in a binary trie; O(n*B) time and O(n*B) space. Inputs are preserved.

function solve(nums, low, high) {
  let maximum = high + 1;
  for (const value of nums) maximum = Math.max(maximum, value);
  const width = Math.floor(Math.log2(Math.max(1, maximum))) + 1;
  const children = [[-1, -1]];
  const counts = [0];
  function below(value, bound) {
    if (bound <= 0) return 0;
    let node = 0;
    let total = 0;
    for (let bit = width - 1; bit >= 0 && node >= 0; bit -= 1) {
      const digit = (value >>> bit) & 1;
      if (((bound >>> bit) & 1) !== 0) {
        const same = children[node][digit];
        if (same >= 0) total += counts[same];
        node = children[node][digit ^ 1];
      } else {
        node = children[node][digit];
      }
    }
    return total;
  }
  let answer = 0;
  for (const value of nums) {
    answer += below(value, high + 1) - below(value, low);
    let node = 0;
    for (let bit = width - 1; bit >= 0; bit -= 1) {
      const digit = (value >>> bit) & 1;
      if (children[node][digit] < 0) {
        children[node][digit] = children.length;
        children.push([-1, -1]);
        counts.push(0);
      }
      node = children[node][digit];
      counts[node] += 1;
    }
  }
  return answer;
}

const countPairs = solve;
class Solution {
  countPairs(nums, low, high) { return solve(nums, low, high); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countPairs };
