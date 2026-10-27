'use strict';

// 637. Average of Levels in Binary Tree.

function solve(root) {
  const answer = [];
  let level = root ? [root] : [];
  while (level.length > 0) {
    let sum = 0;
    const next = [];
    for (const node of level) { sum += node.val; if (node.left) next.push(node.left); if (node.right) next.push(node.right); }
    answer.push(sum / level.length); level = next;
  }
  return answer;
}

const averageOfLevels = solve;
class Solution {
  averageOfLevels(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, averageOfLevels };
