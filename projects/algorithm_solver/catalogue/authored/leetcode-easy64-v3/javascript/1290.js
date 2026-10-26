'use strict';

// 1290. Convert Binary Number in a Linked List to Integer (Easy).
// Specification: https://leetcode.com/problems/convert-binary-number-in-a-linked-list-to-integer/description/
// O(n) time, O(1) space; preserve all input nodes and links.
function solve(head) {
  let result = 0;
  let node = head;
  while (node !== null) {
    result = result * 2 + node.val;
    node = node.next;
  }
  return result;
}

const getDecimalValue = solve;
class Solution {
  getDecimalValue(head) { return solve(head); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getDecimalValue };
