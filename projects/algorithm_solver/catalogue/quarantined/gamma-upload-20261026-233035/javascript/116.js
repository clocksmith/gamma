'use strict';
// 116. Populating Next Right Pointers in Each Node.
class Node {
  constructor(val = 0, left = null, right = null, next = null) {
    this.val = val; this.left = left; this.right = right; this.next = next;
  }
}
function solve(root) {
  let leftmost = root;
  while (leftmost !== null && leftmost.left !== null) {
    let current = leftmost;
    while (current !== null) {
      current.left.next = current.right;
      if (current.next !== null) current.right.next = current.next.left;
      current = current.next;
    }
    leftmost = leftmost.left;
  }
  return root;
}
const connect = solve;
class Solution { connect(root) { return solve(root); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, connect, Node };
