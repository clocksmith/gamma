'use strict';

// 1305. All Elements in Two Binary Search Trees: merge two iterative inorder traversals.
// O(n + m) time and O(n + m) auxiliary space; inputs are read-only.
class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function solve(root1, root2) {
  function values(root) {
    const ordered = [];
    const stack = [];
    let current = root;
    while (current !== null || stack.length) {
      while (current !== null) {
        stack.push(current);
        current = current.left;
      }
      current = stack.pop();
      ordered.push(current.val);
      current = current.right;
    }
    return ordered;
  }
  const first = values(root1);
  const second = values(root2);
  const result = [];
  let left = 0;
  let right = 0;
  while (left < first.length && right < second.length) {
    if (first[left] <= second[right]) {
      result.push(first[left]);
      left += 1;
    } else {
      result.push(second[right]);
      right += 1;
    }
  }
  while (left < first.length) { result.push(first[left]); left += 1; }
  while (right < second.length) { result.push(second[right]); right += 1; }
  return result;
}

const getAllElements = solve;
class Solution {
  getAllElements(root1, root2) { return solve(root1, root2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getAllElements, TreeNode };
