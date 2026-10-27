'use strict';

// 662. Maximum Width of Binary Tree. Normalize complete-tree positions at each level to avoid depth-driven integer growth.

function solve(root) {
  let answer = 0, level = root ? [[root, 0]] : [];
  while (level.length > 0) {
    answer = Math.max(answer, level[level.length - 1][1] - level[0][1] + 1);
    const offset = level[0][1], next = [];
    for (const [node, original] of level) {
      const index = original - offset;
      if (node.left) next.push([node.left, 2 * index]);
      if (node.right) next.push([node.right, 2 * index + 1]);
    }
    level = next;
  }
  return answer;
}

const widthOfBinaryTree = solve;
class Solution {
  widthOfBinaryTree(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, widthOfBinaryTree };
