'use strict';

// 404. Sum of Left Leaves. Iterative traversal; preserves node identities and links.

function solve(root) {
  let answer = 0;
  const stack = root ? [[root, false]] : [];
  while (stack.length > 0) {
    const [node, isLeft] = stack.pop();
    if (!node.left && !node.right && isLeft) answer += node.val;
    if (node.right) stack.push([node.right, false]);
    if (node.left) stack.push([node.left, true]);
  }
  return answer;
}

const sumOfLeftLeaves = solve;
class Solution {
  sumOfLeftLeaves(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOfLeftLeaves };
