'use strict';

// 708. Insert into a Sorted Circular Linked List. Insert in place and retain the supplied head even when it is not the minimum node.

class Node {
  constructor(val = 0, next = null) { this.val = val; this.next = next; }
}

function solve(head, insertVal) {
  if (head === null) {
    const node = new Node(insertVal); node.next = node; return node;
  }
  let current = head;
  while (true) {
    const next = current.next;
    if (current.val <= insertVal && insertVal <= next.val) break;
    if (current.val > next.val && (insertVal >= current.val || insertVal <= next.val)) break;
    current = next;
    if (current === head) break;
  }
  current.next = new Node(insertVal, current.next);
  return head;
}

const insert = solve;
class Solution {
  insert(head, insertVal) { return solve(head, insertVal); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, insert };
