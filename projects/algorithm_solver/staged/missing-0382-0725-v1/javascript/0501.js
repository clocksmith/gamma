'use strict';

// 501. Find Mode in Binary Search Tree. Count equal runs in sorted inorder traversal without modifying the tree.

function solve(root) {
  const stack = [];
  let node = root, previous = null, run = 0, maximum = 0, answer = [];
  while (stack.length > 0 || node) {
    while (node) { stack.push(node); node = node.left; }
    node = stack.pop();
    run = node.val === previous ? run + 1 : 1;
    previous = node.val;
    if (run > maximum) { maximum = run; answer = [node.val]; }
    else if (run === maximum) answer.push(node.val);
    node = node.right;
  }
  return answer;
}

const findMode = solve;
class Solution {
  findMode(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMode };
