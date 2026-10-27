'use strict';

// 671. Second Minimum Node In a Binary Tree.

function solve(root) {
  const minimum = root.val, stack = [root];
  let answer = Infinity;
  while (stack.length > 0) {
    const node = stack.pop();
    if (node.val > minimum) answer = Math.min(answer, node.val);
    else { if (node.left) stack.push(node.left); if (node.right) stack.push(node.right); }
  }
  return answer === Infinity ? -1 : answer;
}

const findSecondMinimumValue = solve;
class Solution {
  findSecondMinimumValue(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findSecondMinimumValue };
