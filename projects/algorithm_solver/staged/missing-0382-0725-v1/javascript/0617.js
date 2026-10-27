'use strict';

// 617. Merge Two Binary Trees. Merge in place into root1 and graft root2-only subtrees; those grafted nodes remain shared.

function solve(root1, root2) {
  if (root1 === null) return root2;
  if (root2 === null) return root1;
  const stack = [[root1, root2]];
  while (stack.length > 0) {
    const [a, b] = stack.pop();
    a.val += b.val;
    if (a.left && b.left) stack.push([a.left, b.left]);
    else if (a.left === null) a.left = b.left;
    if (a.right && b.right) stack.push([a.right, b.right]);
    else if (a.right === null) a.right = b.right;
  }
  return root1;
}

const mergeTrees = solve;
class Solution {
  mergeTrees(root1, root2) { return solve(root1, root2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mergeTrees };
