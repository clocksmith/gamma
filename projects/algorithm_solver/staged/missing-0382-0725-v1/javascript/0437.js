'use strict';

// 437. Path Sum III. Enter/leave DFS frames scope prefix sums to the current ancestor path.

function solve(root, targetSum) {
  const counts = new Map([[0, 1]]);
  let answer = 0;
  const stack = root ? [[root, 0, false]] : [];
  while (stack.length > 0) {
    let [node, total, leaving] = stack.pop();
    if (leaving) {
      const count = counts.get(total) - 1;
      if (count === 0) counts.delete(total); else counts.set(total, count);
      continue;
    }
    total += node.val;
    answer += counts.get(total - targetSum) || 0;
    counts.set(total, (counts.get(total) || 0) + 1);
    stack.push([node, total, true]);
    if (node.right) stack.push([node.right, total, false]);
    if (node.left) stack.push([node.left, total, false]);
  }
  return answer;
}

const pathSum = solve;
class Solution {
  pathSum(root, targetSum) { return solve(root, targetSum); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, pathSum };
