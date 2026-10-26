'use strict';

// 21. Merge Two Sorted Lists (Easy).
// Specification: https://leetcode.com/problems/merge-two-sorted-lists/description/
// O(n + m) time, O(1) space; splice the original disjoint nodes and preserve their values.
function solve(list1, list2) {
  if (list1 === null) return list2;
  if (list2 === null) return list1;
  let head;
  if (list1.val <= list2.val) {
    head = list1;
    list1 = list1.next;
  } else {
    head = list2;
    list2 = list2.next;
  }
  let tail = head;
  while (list1 !== null && list2 !== null) {
    if (list1.val <= list2.val) {
      tail.next = list1;
      list1 = list1.next;
    } else {
      tail.next = list2;
      list2 = list2.next;
    }
    tail = tail.next;
  }
  tail.next = list1 === null ? list2 : list1;
  return head;
}

const mergeTwoLists = solve;
class Solution {
  mergeTwoLists(list1, list2) { return solve(list1, list2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mergeTwoLists };
