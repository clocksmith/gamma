'use strict';
// 142. Linked List Cycle II.
class ListNode { constructor(x = 0, next = null) { this.val = x; this.next = next; } }
function solve(head) {
  let slow = head;
  let fast = head;
  while (fast !== null && fast.next !== null) {
    slow = slow.next; fast = fast.next.next;
    if (slow === fast) {
      let current = head;
      while (current !== slow) { current = current.next; slow = slow.next; }
      return current;
    }
  }
  return null;
}
const detectCycle = solve;
class Solution { detectCycle(head) { return solve(head); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, detectCycle, ListNode };
