'use strict';

// 590. N-ary Tree Postorder Traversal.

function solve(root) {
  const answer = [], stack = root ? [root] : [];
  while (stack.length > 0) {
    const node = stack.pop();
    answer.push(node.val);
    for (const child of node.children || []) stack.push(child);
  }
  return answer.reverse();
}

const postorder = solve;
class Solution {
  postorder(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, postorder };
