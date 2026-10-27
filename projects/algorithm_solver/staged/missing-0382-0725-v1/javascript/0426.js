'use strict';

// 426. Convert Binary Search Tree to Sorted Doubly Linked List. Relink the original nodes in place into a circular list; no replacement nodes.

function solve(root) {
  if (root === null) return null;
  const stack = [];
  let node = root, first = null, previous = null;
  while (stack.length > 0 || node !== null) {
    while (node !== null) { stack.push(node); node = node.left; }
    node = stack.pop();
    const right = node.right;
    node.left = previous;
    if (previous === null) first = node;
    else previous.right = node;
    previous = node;
    node = right;
  }
  first.left = previous;
  previous.right = first;
  return first;
}

const treeToDoublyList = solve;
class Solution {
  treeToDoublyList(root) { return solve(root); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, treeToDoublyList };
