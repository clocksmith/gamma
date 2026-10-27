'use strict';

// 445. Add Two Numbers II. Add from digit stacks; never reverse or mutate either input list.

class ListNode {
  constructor(val = 0, next = null) { this.val = val; this.next = next; }
}

function solve(l1, l2) {
  const a = [], b = [];
  for (let node = l1; node; node = node.next) a.push(node.val);
  for (let node = l2; node; node = node.next) b.push(node.val);
  let head = null, carry = 0;
  while (a.length > 0 || b.length > 0 || carry > 0) {
    const total = carry + (a.length > 0 ? a.pop() : 0) + (b.length > 0 ? b.pop() : 0);
    carry = Math.floor(total / 10);
    head = new ListNode(total % 10, head);
  }
  return head;
}

const addTwoNumbers = solve;
class Solution {
  addTwoNumbers(l1, l2) { return solve(l1, l2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, addTwoNumbers };
