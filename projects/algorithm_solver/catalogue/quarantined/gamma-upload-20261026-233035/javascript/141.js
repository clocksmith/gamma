'use strict';
// 141. Linked List Cycle.
class ListNode { constructor(x = 0, next = null) { this.val = x; this.next = next; } }
function solve(head) {
  let slow = head;
  let fast = head;
  while (fast !== null && fast.next !== null) {
    slow = slow.next; fast = fast.next.next;
    if (slow === fast) return true;
  }
  return false;
}
const hasCycle = solve;
class Solution { hasCycle(head) { return solve(head); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, hasCycle, ListNode };
