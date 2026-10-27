'use strict';

// 3902. Zigzag Level Sum of Binary Tree.
// Specification: https://leetcode.com/problems/zigzag-level-sum-of-binary-tree/description/
// O(n) time and O(width) auxiliary space; all nodes still supply the next level after a summation stop. Inputs are preserved.
function solve(root) {
  if (root === null) return [];
  let level = [root];
  let odd = true;
  const answer = [];
  while (level.length > 0) {
    let sum = 0;
    if (odd) {
      for (const node of level) { if (!node.left) break; sum += node.val; }
    } else {
      for (let index = level.length - 1; index >= 0; index--) {
        if (!level[index].right) break;
        sum += level[index].val;
      }
    }
    answer.push(sum);
    const next = [];
    for (const node of level) {
      if (node.left) next.push(node.left);
      if (node.right) next.push(node.right);
    }
    level = next;
    odd = !odd;
  }
  return answer;
}

if (typeof module !== 'undefined') module.exports = { solve };
