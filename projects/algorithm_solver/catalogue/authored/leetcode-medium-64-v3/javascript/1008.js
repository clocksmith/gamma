'use strict';

// 1008. Construct Binary Search Tree from Preorder Traversal: use an ancestor stack to attach each distinct value.
// O(n) time and O(n) auxiliary space excluding the returned tree; inputs are read-only.
class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function solve(preorder) {
  if (preorder.length === 0) return null;
  const root = new TreeNode(preorder[0]);
  const stack = [root];
  for (let index = 1; index < preorder.length; index += 1) {
    const node = new TreeNode(preorder[index]);
    if (node.val < stack[stack.length - 1].val) stack[stack.length - 1].left = node;
    else {
      let parent = stack.pop();
      while (stack.length && stack[stack.length - 1].val < node.val) parent = stack.pop();
      parent.right = node;
    }
    stack.push(node);
  }
  return root;
}

const bstFromPreorder = solve;
class Solution {
  bstFromPreorder(preorder) { return solve(preorder); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, bstFromPreorder, TreeNode };
