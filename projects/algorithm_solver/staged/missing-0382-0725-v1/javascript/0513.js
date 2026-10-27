'use strict';

// 513. Find Bottom Left Tree Value.

function solve(root) {
  let level = [root], answer = root.val;
  while (level.length > 0) {
    answer = level[0].val;
    const next = [];
    for (const node of level) { if (node.left) next.push(node.left); if (node.right) next.push(node.right); }
    level = next;
  }
  return answer;
}

const findBottomLeftValue = solve;
class Solution {
  findBottomLeftValue(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findBottomLeftValue };
