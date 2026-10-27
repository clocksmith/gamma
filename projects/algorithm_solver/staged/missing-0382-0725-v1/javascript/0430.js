'use strict';

// 430. Flatten a Multilevel Doubly Linked List. Depth-first in-place relinking preserves every original list node.

function solve(head) {
  if (head === null) return null;
  const stack = [head];
  let previous = null;
  while (stack.length > 0) {
    const node = stack.pop();
    if (node.next) stack.push(node.next);
    if (node.child) stack.push(node.child);
    node.prev = previous;
    if (previous) previous.next = node;
    node.child = null;
    previous = node;
  }
  previous.next = null;
  return head;
}

const flatten = solve;
class Solution {
  flatten(head) { return solve(head); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, flatten };
