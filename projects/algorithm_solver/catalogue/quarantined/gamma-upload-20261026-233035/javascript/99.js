'use strict';
// 99. Recover Binary Search Tree.
class TreeNode {
  constructor(val = 0, left = null, right = null) { this.val = val; this.left = left; this.right = right; }
}
function solve(root) {
  let first = null;
  let second = null;
  let previous = null;
  const stack = [];
  let current = root;
  while (current !== null || stack.length) {
    while (current !== null) { stack.push(current); current = current.left; }
    current = stack.pop();
    if (previous !== null && previous.val > current.val) {
      if (first === null) first = previous;
      second = current;
    }
    previous = current;
    current = current.right;
  }
  if (first !== null) [first.val, second.val] = [second.val, first.val];
}
const recoverTree = solve;
class Solution { recoverTree(root) { solve(root); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, recoverTree, TreeNode };
