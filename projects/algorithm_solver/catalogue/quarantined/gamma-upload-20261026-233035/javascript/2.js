'use strict';
// 2. Add Two Numbers.

class ListNode {
  constructor(val = 0, next = null) {
    this.val = val;
    this.next = next;
  }
}
function solve(l1, l2) {
  const dummy = new ListNode();
  let tail = dummy;
  let carry = 0;
  while (l1 !== null || l2 !== null || carry !== 0) {
    let total = carry;
    if (l1 !== null) { total += l1.val; l1 = l1.next; }
    if (l2 !== null) { total += l2.val; l2 = l2.next; }
    carry = Math.floor(total / 10);
    tail.next = new ListNode(total % 10);
    tail = tail.next;
  }
  return dummy.next;
}
const addTwoNumbers = solve;
class Solution { addTwoNumbers(l1, l2) { return solve(l1, l2); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, addTwoNumbers, ListNode };
