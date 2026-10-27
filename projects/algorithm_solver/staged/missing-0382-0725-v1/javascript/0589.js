'use strict';

// 589. N-ary Tree Preorder Traversal.

function solve(root) {
  const answer = [], stack = root ? [root] : [];
  while (stack.length > 0) {
    const node = stack.pop(), children = node.children || [];
    answer.push(node.val);
    for (let i = children.length - 1; i >= 0; i -= 1) stack.push(children[i]);
  }
  return answer;
}

const preorder = solve;
class Solution {
  preorder(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, preorder };
