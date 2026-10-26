'use strict';

// 2816. Double a Number Represented as a Linked List: propagate decimal carries backward and construct nonaliasing output nodes.
// O(n) time and O(n) auxiliary space excluding returned nodes; inputs are read-only.
class ListNode {
  constructor(val = 0, next = null) {
    this.val = val;
    this.next = next;
  }
}

function solve(head) {
  const digits = [];
  for (let current = head; current !== null; current = current.next) digits.push(current.val);
  let result = null;
  let carry = 0;
  for (let index = digits.length - 1; index >= 0; index -= 1) {
    const value = 2 * digits[index] + carry;
    result = new ListNode(value % 10, result);
    carry = Math.floor(value / 10);
  }
  if (carry !== 0) result = new ListNode(carry, result);
  return result;
}

const doubleIt = solve;
class Solution {
  doubleIt(head) { return solve(head); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, doubleIt, ListNode };
