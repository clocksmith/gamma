'use strict';

// 2074. Reverse Nodes in Even Length Groups: copy values into fresh nodes using each actual group length.
// O(n) time and O(n) auxiliary space excluding the returned list; inputs are read-only.
class ListNode {
  constructor(val = 0, next = null) {
    this.val = val;
    this.next = next;
  }
}

function solve(head) {
  const values = [];
  for (let current = head; current !== null; current = current.next) values.push(current.val);
  const dummy = new ListNode();
  let tail = dummy;
  let left = 0;
  let requested = 1;
  while (left < values.length) {
    const right = Math.min(values.length, left + requested);
    const reversed = (right - left) % 2 === 0;
    for (let offset = 0; offset < right - left; offset += 1) {
      const index = reversed ? right - 1 - offset : left + offset;
      tail.next = new ListNode(values[index]);
      tail = tail.next;
    }
    left = right;
    requested += 1;
  }
  return dummy.next;
}

const reverseEvenLengthGroups = solve;
class Solution {
  reverseEvenLengthGroups(head) { return solve(head); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseEvenLengthGroups, ListNode };
