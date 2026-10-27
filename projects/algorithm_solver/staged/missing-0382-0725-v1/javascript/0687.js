'use strict';

// 687. Longest Univalue Path. Postorder chain lengths are measured in edges, not nodes.

function solve(root) {
  const chains = new Map(), stack = root ? [[root, false]] : [];
  let answer = 0;
  while (stack.length > 0) {
    const [node, ready] = stack.pop();
    if (!ready) {
      stack.push([node, true]); if (node.right) stack.push([node.right, false]); if (node.left) stack.push([node.left, false]);
    } else {
      const left = node.left && node.left.val === node.val ? chains.get(node.left) + 1 : 0;
      const right = node.right && node.right.val === node.val ? chains.get(node.right) + 1 : 0;
      chains.set(node, Math.max(left, right)); answer = Math.max(answer, left + right);
    }
  }
  return answer;
}

const longestUnivaluePath = solve;
class Solution {
  longestUnivaluePath(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestUnivaluePath };
