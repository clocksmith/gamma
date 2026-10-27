'use strict';

// 450. Delete Node in a BST. Update the supplied BST in place; copy a successor value only for a two-child deletion.

function solve(root, key) {
  let parent = null, node = root;
  while (node !== null && node.val !== key) {
    parent = node; node = key < node.val ? node.left : node.right;
  }
  if (node === null) return root;
  if (node.left !== null && node.right !== null) {
    let successorParent = node, successor = node.right;
    while (successor.left !== null) { successorParent = successor; successor = successor.left; }
    node.val = successor.val;
    parent = successorParent; node = successor;
  }
  const child = node.left !== null ? node.left : node.right;
  if (parent === null) return child;
  if (parent.left === node) parent.left = child;
  else parent.right = child;
  return root;
}

const deleteNode = solve;
class Solution {
  deleteNode(root, key) { return solve(root, key); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, deleteNode };
