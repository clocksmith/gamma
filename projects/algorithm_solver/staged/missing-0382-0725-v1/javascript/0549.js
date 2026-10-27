'use strict';

// 549. Binary Tree Longest Consecutive Sequence II. Combine increasing and decreasing child paths in iterative postorder.

function solve(root) {
  let answer = 0;
  const lengths = new Map(), stack = root ? [[root, false]] : [];
  while (stack.length > 0) {
    const [node, ready] = stack.pop();
    if (!ready) {
      stack.push([node, true]);
      if (node.right) stack.push([node.right, false]);
      if (node.left) stack.push([node.left, false]);
      continue;
    }
    let increasing = 1, decreasing = 1;
    for (const child of [node.left, node.right]) if (child) {
      const [inc, dec] = lengths.get(child);
      if (child.val === node.val + 1) increasing = Math.max(increasing, inc + 1);
      if (child.val === node.val - 1) decreasing = Math.max(decreasing, dec + 1);
    }
    lengths.set(node, [increasing, decreasing]);
    answer = Math.max(answer, increasing + decreasing - 1);
  }
  return answer;
}

const longestConsecutive = solve;
class Solution {
  longestConsecutive(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestConsecutive };
