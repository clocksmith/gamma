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
  return plusOneInPlace(cloneList(head));
}

// Copies a caller's linked list so solve never mutates or aliases it; a node
// reached twice (cycle) is rejected. The copy keeps each node's prototype.
// Charged: O(n) time, O(n) auxiliary space.
function cloneList(head) {
  const seen = new Set();
  const sentinel = new ListNode();
  let tail = sentinel;
  for (let cur = head; cur !== null && cur !== undefined; cur = cur.next) {
    if (seen.has(cur)) throw new TypeError("plusOne: input list has a cycle");
    seen.add(cur);
    const copy = Object.create(Object.getPrototypeOf(cur));
    copy.val = cur.val;
    copy.next = null;
    tail.next = copy;
    tail = copy;
  }
  return sentinel.next;
}

// Adds one to the digits of a list the caller of this helper owns.
function plusOneInPlace(head) {
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

// Official LeetCode ABI: increments the caller's list in place and returns its
// head (native_effects.mutates_inputs = true). Digit arrays use the pure path.
function plusOne(head) {
  if (Array.isArray(head)) return solve(head);
  return plusOneInPlace(head === undefined ? null : head);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.plusOne = plusOne;
module.exports.ListNode = ListNode;
if (typeof Solution !== "undefined") solve.Solution = Solution;
