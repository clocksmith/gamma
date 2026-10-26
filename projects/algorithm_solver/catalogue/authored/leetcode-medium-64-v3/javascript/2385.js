'use strict';

// 2385. Amount of Time for Binary Tree to Be Infected: traverse parent and child links outward from the starting node.
// O(n) time and O(n) auxiliary space; inputs are read-only.
class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function solve(root, start) {
  if (root === null) return 0;
  const parents = new Map([[root, null]]);
  const stack = [root];
  let origin = null;
  while (stack.length) {
    const node = stack.pop();
    if (node.val === start) origin = node;
    for (const child of [node.left, node.right]) {
      if (child !== null) {
        parents.set(child, node);
        stack.push(child);
      }
    }
  }
  if (origin === null) throw new Error('start value is absent from the tree');
  const seen = new Set([origin]);
  let frontier = [origin];
  let minutes = -1;
  while (frontier.length) {
    const following = [];
    minutes += 1;
    for (const node of frontier) {
      for (const neighbor of [node.left, node.right, parents.get(node)]) {
        if (neighbor !== null && !seen.has(neighbor)) {
          seen.add(neighbor);
          following.push(neighbor);
        }
      }
    }
    frontier = following;
  }
  return minutes;
}

const amountOfTime = solve;
class Solution {
  amountOfTime(root, start) { return solve(root, start); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, amountOfTime, TreeNode };
