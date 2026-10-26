'use strict';

// 2487. Remove Nodes From Linked List: keep a decreasing stack of values and build an independent result list.
// O(n) time and O(n) auxiliary space; inputs are read-only.
class ListNode {
  constructor(val = 0, next = null) {
    this.val = val;
    this.next = next;
  }
}

function solve(head) {
  const values = [];
  for (let node = head; node !== null; node = node.next) {
    while (values.length && values[values.length - 1] < node.val) values.pop();
    values.push(node.val);
  }
  let result = null;
  for (let index = values.length - 1; index >= 0; index -= 1) {
    result = new ListNode(values[index], result);
  }
  return result;
}

const removeNodes = solve;
class Solution {
  removeNodes(head) { return solve(head); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, removeNodes, ListNode };
