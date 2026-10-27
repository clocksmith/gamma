'use strict';

// 429. N-ary Tree Level Order Traversal. Breadth-first traversal; preserves the input tree.

function solve(root) {
  const answer = [];
  let level = root ? [root] : [];
  while (level.length > 0) {
    answer.push(level.map(node => node.val));
    const next = [];
    for (const node of level) for (const child of node.children || []) next.push(child);
    level = next;
  }
  return answer;
}

const levelOrder = solve;
class Solution {
  levelOrder(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, levelOrder };
