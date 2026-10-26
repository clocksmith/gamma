'use strict';

// 998. Maximum Binary Tree II: copy the tree and insert along its right spine.
// O(n) time and O(n) auxiliary space including the nonaliasing copy; inputs are read-only.
class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function solve(root, val) {
  const inserted = new TreeNode(val);
  if (root === null) return inserted;
  const result = new TreeNode(root.val);
  const stack = [[root, result]];
  while (stack.length) {
    const [original, copied] = stack.pop();
    if (original.left !== null) {
      copied.left = new TreeNode(original.left.val);
      stack.push([original.left, copied.left]);
    }
    if (original.right !== null) {
      copied.right = new TreeNode(original.right.val);
      stack.push([original.right, copied.right]);
    }
  }
  if (val > result.val) {
    inserted.left = result;
    return inserted;
  }
  let current = result;
  while (current.right !== null && current.right.val > val) current = current.right;
  inserted.left = current.right;
  current.right = inserted;
  return result;
}

const insertIntoMaxTree = solve;
class Solution {
  insertIntoMaxTree(root, val) { return solve(root, val); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, insertIntoMaxTree, TreeNode };
