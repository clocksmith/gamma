"use strict";

function ListNode(val, next) {
  this.val = val === undefined ? 0 : val;
  this.next = next === undefined ? null : next;
}

function relink(head) {
  if (!head || !head.next) return head;
  let odd = head;
  let even = head.next;
  const evenHead = even;
  while (even !== null && even.next !== null) {
    odd.next = even.next;
    odd = odd.next;
    even.next = odd.next;
    even = even.next;
  }
  odd.next = evenHead;
  return head;
}

function solve(head) {
  if (Array.isArray(head)) {
    if (head.length === 0) return [];
    const nodes = head.map((v) => new ListNode(v));
    for (let i = 0; i < nodes.length - 1; i++) nodes[i].next = nodes[i + 1];
    let cur = relink(nodes[0]);
    const out = [];
    while (cur !== null) {
      out.push(cur.val);
      cur = cur.next;
    }
    return out;
  }
  return relink(head);
}

function oddEvenList(head) {
  return solve(head);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.oddEvenList = oddEvenList;
module.exports.ListNode = ListNode;
