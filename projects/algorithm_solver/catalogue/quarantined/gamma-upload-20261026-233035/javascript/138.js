'use strict';
// 138. Copy List with Random Pointer.
class Node {
  constructor(x = 0, next = null, random = null) { this.val = x; this.next = next; this.random = random; }
}
function solve(head) {
  let current = head;
  while (current !== null) {
    current.next = new Node(current.val, current.next);
    current = current.next.next;
  }
  current = head;
  while (current !== null) {
    const copy = current.next;
    copy.random = current.random === null ? null : current.random.next;
    current = copy.next;
  }
  const dummy = new Node();
  let tail = dummy;
  current = head;
  while (current !== null) {
    const copy = current.next;
    current.next = copy.next;
    tail.next = copy;
    tail = copy;
    current = current.next;
  }
  return dummy.next;
}
const copyRandomList = solve;
class Solution { copyRandomList(head) { return solve(head); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, copyRandomList, Node };
