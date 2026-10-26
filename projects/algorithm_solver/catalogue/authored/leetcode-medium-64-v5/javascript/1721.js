'use strict';

// 1721. Swapping Nodes in a Linked List: copy the list before swapping the two selected values.
// O(n) time and O(n) output space with O(1) auxiliary space; inputs are read-only.
class ListNode {
  constructor(val = 0, next = null) {
    this.val = val;
    this.next = next;
  }
}

function solve(head, k) {
  const dummy = new ListNode();
  let tail = dummy;
  let current = head;
  let length = 0;
  while (current !== null) {
    tail.next = new ListNode(current.val);
    tail = tail.next;
    current = current.next;
    length += 1;
  }
  let first = dummy.next;
  let second = dummy.next;
  for (let index = 1; index < k; index += 1) first = first.next;
  for (let index = 0; index < length - k; index += 1) second = second.next;
  [first.val, second.val] = [second.val, first.val];
  return dummy.next;
}

const swapNodes = solve;
class Solution {
  swapNodes(head, k) { return solve(head, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, swapNodes, ListNode };
