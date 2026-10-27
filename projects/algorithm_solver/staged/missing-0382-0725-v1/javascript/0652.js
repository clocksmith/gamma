'use strict';

// 652. Find Duplicate Subtrees. Intern subtree identities and return one original node per duplicated structure.

function solve(root) {
  const identities = new Map(), nodeIds = new Map(), counts = new Map(), answer = [];
  const stack = root ? [[root, false]] : [];
  while (stack.length > 0) {
    const [node, ready] = stack.pop();
    if (!ready) {
      stack.push([node, true]);
      if (node.right) stack.push([node.right, false]);
      if (node.left) stack.push([node.left, false]);
      continue;
    }
    const signature = `${node.val},${nodeIds.get(node.left) || 0},${nodeIds.get(node.right) || 0}`;
    if (!identities.has(signature)) identities.set(signature, identities.size + 1);
    const id = identities.get(signature), count = (counts.get(id) || 0) + 1;
    nodeIds.set(node, id); counts.set(id, count);
    if (count === 2) answer.push(node);
  }
  return answer;
}

const findDuplicateSubtrees = solve;
class Solution {
  findDuplicateSubtrees(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findDuplicateSubtrees };
