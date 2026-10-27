'use strict';

// 655. Print Binary Tree.

function solve(root) {
  if (root === null) return [];
  let height = 0;
  const pending = [[root, 1]];
  while (pending.length > 0) {
    const [node, depth] = pending.pop(); height = Math.max(height, depth);
    if (node.left) pending.push([node.left, depth + 1]);
    if (node.right) pending.push([node.right, depth + 1]);
  }
  const width = 2 ** height - 1, answer = Array.from({length: height}, () => Array(width).fill(''));
  const stack = [[root, 0, 0, width - 1]];
  while (stack.length > 0) {
    const [node, row, left, right] = stack.pop(), middle = Math.floor((left + right) / 2);
    answer[row][middle] = String(node.val);
    if (node.right) stack.push([node.right, row + 1, middle + 1, right]);
    if (node.left) stack.push([node.left, row + 1, left, middle - 1]);
  }
  return answer;
}

const printTree = solve;
class Solution {
  printTree(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, printTree };
