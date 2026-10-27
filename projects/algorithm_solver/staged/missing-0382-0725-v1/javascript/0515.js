'use strict';

// 515. Find Largest Value in Each Tree Row.

function solve(root) {
  const answer = [];
  let level = root ? [root] : [];
  while (level.length > 0) {
    let maximum = -Infinity;
    const next = [];
    for (const node of level) {
      maximum = Math.max(maximum, node.val);
      if (node.left) next.push(node.left); if (node.right) next.push(node.right);
    }
    answer.push(maximum); level = next;
  }
  return answer;
}

const largestValues = solve;
class Solution {
  largestValues(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, largestValues };
