'use strict';

// 606. Construct String from Binary Tree. Iterative preorder emits the empty left pair only when needed to preserve structure.

function solve(root) {
  if (root === null) return '';
  const parts = [], stack = [root];
  while (stack.length > 0) {
    const item = stack.pop();
    if (typeof item === 'string') { parts.push(item); continue; }
    parts.push(String(item.val));
    if (item.right !== null) stack.push(')', item.right, '(');
    if (item.left !== null || item.right !== null) {
      stack.push(')'); if (item.left !== null) stack.push(item.left); stack.push('(');
    }
  }
  return parts.join('');
}

const tree2str = solve;
class Solution {
  tree2str(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, tree2str };
