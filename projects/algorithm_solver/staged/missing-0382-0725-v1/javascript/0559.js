'use strict';

// 559. Maximum Depth of N-ary Tree.

function solve(root) {
  let answer = 0;
  const stack = root ? [[root, 1]] : [];
  while (stack.length > 0) {
    const [node, depth] = stack.pop();
    answer = Math.max(answer, depth);
    for (const child of node.children || []) stack.push([child, depth + 1]);
  }
  return answer;
}

const maxDepth = solve;
class Solution {
  maxDepth(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxDepth };
