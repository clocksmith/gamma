'use strict';
// 143. Reorder List.
class ListNode { constructor(val = 0, next = null) { this.val = val; this.next = next; } }
function solve(head) {
  if (head === null || head.next === null) return;
  let slow = head; let fast = head;
  while (fast.next !== null && fast.next.next !== null) { slow = slow.next; fast = fast.next.next; }
  let current = slow.next; slow.next = null;
  let previous = null;
  while (current !== null) {
    const following = current.next; current.next = previous; previous = current; current = following;
  }
  let first = head; let second = previous;
  while (second !== null) {
    const firstNext = first.next; const secondNext = second.next;
    first.next = second; second.next = firstNext;
    first = firstNext; second = secondNext;
  }
}
const reorderList = solve;
class Solution { reorderList(head) { solve(head); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reorderList, ListNode };
