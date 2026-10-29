"use strict";

function solve(head) {
  if (Array.isArray(head)) return head.slice().reverse();
  const stack = [];
  let cur = head;
  while (cur !== null && cur !== undefined) {
    stack.push(cur);
    cur = cur.getNext();
  }
  while (stack.length > 0) {
    stack.pop().printValue();
  }
  return null;
}

function printLinkedListInReverse(head) {
  return solve(head);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.printLinkedListInReverse = printLinkedListInReverse;
