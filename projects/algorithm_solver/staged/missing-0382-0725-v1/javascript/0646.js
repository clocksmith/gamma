'use strict';

// 646. Maximum Length of Pair Chain.

function solve(pairs) {
  let end = -Infinity, answer = 0;
  for (const [left, right] of pairs.slice().sort((a, b) => a[1] - b[1])) {
    if (left > end) { answer += 1; end = right; }
  }
  return answer;
}

const findLongestChain = solve;
class Solution {
  findLongestChain(pairs) { return solve(pairs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findLongestChain };
