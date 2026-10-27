'use strict';
// 160. Intersection of Two Linked Lists.
class ListNode { constructor(x = 0, next = null) { this.val = x; this.next = next; } }
function solve(headA, headB) {
  let left = headA; let right = headB;
  while (left !== right) {
    left = left === null ? headB : left.next;
    right = right === null ? headA : right.next;
  }
  return left;
}
const getIntersectionNode = solve;
class Solution { getIntersectionNode(headA, headB) { return solve(headA, headB); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, getIntersectionNode, ListNode };
