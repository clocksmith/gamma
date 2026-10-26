'use strict';

// 3864. Minimum Cost to Partition a Binary String.
// O(n) time and O(n) space; only equal even-length splits, with recursion depth at most log2(n).
function solve(s, encCost, flatCost) {
  const prefix = [0];
  for (const char of s) prefix.push(prefix[prefix.length - 1] + Number(char === '1'));
  function partition(left, right) {
    const sensitive = prefix[right] - prefix[left];
    if (sensitive === 0) return flatCost;
    const length = right - left;
    let cost = length * sensitive * encCost;
    if (length % 2 === 0) {
      const middle = (left + right) / 2;
      cost = Math.min(cost, partition(left, middle) + partition(middle, right));
    }
    return cost;
  }
  return partition(0, s.length);
}

const minCost = solve;
class Solution {
  minCost(s, encCost, flatCost) { return solve(s, encCost, flatCost); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minCost };
