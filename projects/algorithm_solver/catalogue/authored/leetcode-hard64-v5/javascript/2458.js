'use strict';

// 2458. Height of Binary Tree After Subtree Removal Queries. Exclude contiguous preorder subtree intervals using prefix and suffix depth maxima; O(n+q) time and O(n) auxiliary space. Inputs are preserved.

function solve(root, queries) {
  const entry = new Map();
  const leave = new Map();
  const depths = [];
  const stack = [[root, 0, false]];
  while (stack.length > 0) {
    const [node, depth, exiting] = stack.pop();
    if (exiting) { leave.set(node.val, depths.length); continue; }
    entry.set(node.val, depths.length);
    depths.push(depth);
    stack.push([node, depth, true]);
    if (node.right != null) stack.push([node.right, depth + 1, false]);
    if (node.left != null) stack.push([node.left, depth + 1, false]);
  }
  const size = depths.length;
  const prefix = Array(size + 1).fill(-1);
  const suffix = Array(size + 1).fill(-1);
  for (let index = 0; index < size; index += 1) prefix[index + 1] = Math.max(prefix[index], depths[index]);
  for (let index = size - 1; index >= 0; index -= 1) suffix[index] = Math.max(suffix[index + 1], depths[index]);
  return queries.map(value => Math.max(prefix[entry.get(value)], suffix[leave.get(value)]));
}

const treeQueries = solve;
class Solution {
  treeQueries(root, queries) { return solve(root, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, treeQueries };
