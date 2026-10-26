'use strict';

// 2807. Insert Greatest Common Divisors in Linked List: build a fresh list with each adjacent-pair gcd inserted.
// O(n log M) time and O(1) auxiliary space excluding returned nodes; inputs are read-only.
class ListNode {
  constructor(val = 0, next = null) {
    this.val = val;
    this.next = next;
  }
}

function solve(head) {
  function gcd(left, right) {
    while (right !== 0) [left, right] = [right, left % right];
    return left;
  }
  const dummy = new ListNode();
  let tail = dummy;
  for (let current = head; current !== null; current = current.next) {
    tail.next = new ListNode(current.val);
    tail = tail.next;
    if (current.next !== null) {
      tail.next = new ListNode(gcd(current.val, current.next.val));
      tail = tail.next;
    }
  }
  return dummy.next;
}

const insertGreatestCommonDivisors = solve;
class Solution {
  insertGreatestCommonDivisors(head) { return solve(head); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, insertGreatestCommonDivisors, ListNode };
