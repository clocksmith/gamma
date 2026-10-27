'use strict';

// 508. Most Frequent Subtree Sum. Postorder subtree sums; returned ties are sorted for deterministic cross-language output.

function solve(root) {
  if (!root) return [];
  const sums = new Map(), counts = new Map(), stack = [[root, false]];
  while (stack.length > 0) {
    const [node, ready] = stack.pop();
    if (!ready) {
      stack.push([node, true]);
      if (node.right) stack.push([node.right, false]);
      if (node.left) stack.push([node.left, false]);
    } else {
      const total = node.val + (sums.get(node.left) || 0) + (sums.get(node.right) || 0);
      sums.set(node, total); counts.set(total, (counts.get(total) || 0) + 1);
    }
  }
  let maximum = 0;
  for (const count of counts.values()) maximum = Math.max(maximum, count);
  return Array.from(counts).filter(([, count]) => count === maximum).map(([total]) => total).sort((a, b) => a - b);
}

const findFrequentTreeSum = solve;
class Solution {
  findFrequentTreeSum(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findFrequentTreeSum };
