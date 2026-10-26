'use strict';

// 2807. Insert Greatest Common Divisors in Linked List: insert between original adjacent nodes.
// O(n log M) time and O(1) auxiliary space excluding inserted nodes; originals are retained.
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
  let current = head;
  while (current !== null && current.next !== null) {
    const following = current.next;
    current.next = new ListNode(gcd(current.val, following.val), following);
    current = following;
  }
  return head;
}

const insertGreatestCommonDivisors = solve;
class Solution {
  insertGreatestCommonDivisors(head) { return solve(head); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, insertGreatestCommonDivisors, ListNode };
