'use strict';
// 206. Reverse Linked List.
class ListNode { constructor(val = 0, next = null) { this.val = val; this.next = next; } }
function solve(head) {
  let previous = null; let current = head;
  while (current !== null) {
    const following = current.next; current.next = previous; previous = current; current = following;
  }
  return previous;
}
const reverseList = solve;
class Solution { reverseList(head) { return solve(head); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseList, ListNode };
