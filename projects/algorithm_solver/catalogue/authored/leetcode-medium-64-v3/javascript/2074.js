'use strict';

// 2074. Reverse Nodes in Even Length Groups: relink original nodes by actual group length.
// O(n) time and O(1) auxiliary space; original node links are modified.
class ListNode {
  constructor(val = 0, next = null) {
    this.val = val;
    this.next = next;
  }
}

function solve(head) {
  const dummy = new ListNode(0, head);
  let previous = dummy;
  let current = head;
  let requested = 1;
  while (current !== null) {
    let following = current;
    let last = current;
    let count = 0;
    while (following !== null && count < requested) {
      last = following;
      following = following.next;
      count += 1;
    }
    if (count % 2 === 0) {
      const tail = current;
      let reversed = following;
      for (let index = 0; index < count; index += 1) {
        const next = current.next;
        current.next = reversed;
        reversed = current;
        current = next;
      }
      previous.next = reversed;
      previous = tail;
    } else {
      previous = last;
    }
    current = following;
    requested += 1;
  }
  return dummy.next;
}

const reverseEvenLengthGroups = solve;
class Solution {
  reverseEvenLengthGroups(head) { return solve(head); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, reverseEvenLengthGroups, ListNode };
