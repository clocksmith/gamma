'use strict';

// 1609. Even Odd Tree: validate parity and strict ordering one level at a time.
// O(n) time and O(w) auxiliary space for maximum level width w; inputs are read-only.
class TreeNode {
  constructor(val = 0, left = null, right = null) {
    this.val = val;
    this.left = left;
    this.right = right;
  }
}

function solve(root) {
  if (root === null) return true;
  let level = [root];
  let evenLevel = true;
  while (level.length) {
    let previous = evenLevel ? -Infinity : Infinity;
    const following = [];
    for (const node of level) {
      if (evenLevel) {
        if (node.val % 2 === 0 || node.val <= previous) return false;
      } else if (node.val % 2 !== 0 || node.val >= previous) return false;
      previous = node.val;
      if (node.left !== null) following.push(node.left);
      if (node.right !== null) following.push(node.right);
    }
    level = following;
    evenLevel = !evenLevel;
  }
  return true;
}

const isEvenOddTree = solve;
class Solution {
  isEvenOddTree(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, isEvenOddTree, TreeNode };
