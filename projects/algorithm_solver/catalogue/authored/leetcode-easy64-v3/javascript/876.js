'use strict';

// 876. Middle of the Linked List (Easy).
// Specification: https://leetcode.com/problems/middle-of-the-linked-list/description/
// O(n) time, O(1) space; return the original middle node without changing links.
function solve(head) {
  let slow = head;
  let fast = head;
  while (fast !== null && fast.next !== null) {
    slow = slow.next;
    fast = fast.next.next;
  }
  return slow;
}

const middleNode = solve;
class Solution {
  middleNode(head) { return solve(head); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, middleNode };
