"use strict";

function ListNode(val, next) {
  this.val = val === undefined ? 0 : val;
  this.next = next === undefined ? null : next;
}

function solve(head) {
  if (Array.isArray(head)) {
    const arr = head.slice();
    for (let i = arr.length - 1; i >= 0; i--) {
      if (arr[i] < 9) {
        arr[i]++;
        return arr;
      }
      arr[i] = 0;
    }
    return [1].concat(arr);
  }
  const sentinel = new ListNode(0, head);
  let notNine = sentinel;
  let cur = head;
  while (cur !== null && cur !== undefined) {
    if (cur.val !== 9) notNine = cur;
    cur = cur.next;
  }
  notNine.val++;
  cur = notNine.next;
  while (cur !== null && cur !== undefined) {
    cur.val = 0;
    cur = cur.next;
  }
  return sentinel.val !== 0 ? sentinel : sentinel.next;
}

function plusOne(head) {
  return solve(head);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.plusOne = plusOne;
module.exports.ListNode = ListNode;
