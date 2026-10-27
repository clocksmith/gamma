'use strict';
// 117. Populating Next Right Pointers in Each Node II.
class Node {
  constructor(val = 0, left = null, right = null, next = null) {
    this.val = val; this.left = left; this.right = right; this.next = next;
  }
}
function solve(root) {
  let current = root;
  while (current !== null) {
    const dummy = new Node();
    let tail = dummy;
    while (current !== null) {
      if (current.left !== null) { tail.next = current.left; tail = tail.next; }
      if (current.right !== null) { tail.next = current.right; tail = tail.next; }
      current = current.next;
    }
    current = dummy.next;
  }
  return root;
}
const connect = solve;
class Solution { connect(root) { return solve(root); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, connect, Node };
