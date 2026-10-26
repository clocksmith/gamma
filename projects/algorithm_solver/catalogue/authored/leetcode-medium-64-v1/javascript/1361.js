'use strict';

// 1361. Validate Binary Tree Nodes: require unique parents and one root that reaches every node.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(n, leftChild, rightChild) {
  const indegree = new Uint8Array(n);
  for (const children of [leftChild, rightChild]) {
    for (const child of children) {
      if (child !== -1) {
        indegree[child] += 1;
        if (indegree[child] > 1) return false;
      }
    }
  }
  let root = -1;
  for (let node = 0; node < n; node += 1) {
    if (indegree[node] === 0) {
      if (root !== -1) return false;
      root = node;
    }
  }
  if (root === -1) return false;
  const seen = new Uint8Array(n);
  const stack = [root];
  let visited = 0;
  while (stack.length) {
    const node = stack.pop();
    if (seen[node]) return false;
    seen[node] = 1;
    visited += 1;
    if (leftChild[node] !== -1) stack.push(leftChild[node]);
    if (rightChild[node] !== -1) stack.push(rightChild[node]);
  }
  return visited === n;
}

const validateBinaryTreeNodes = solve;
class Solution {
  validateBinaryTreeNodes(n, leftChild, rightChild) { return solve(n, leftChild, rightChild); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, validateBinaryTreeNodes };
