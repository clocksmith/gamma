"use strict";

function ListNode(val, next) {
  this.val = val === undefined ? 0 : val;
  this.next = next === undefined ? null : next;
}

function deleteNodesLink(head, m, n) {
  let cur = head;
  while (cur !== null) {
    for (let i = 1; i < m && cur !== null; i++) cur = cur.next;
    if (cur === null) break;
    let nxt = cur.next;
    for (let i = 0; i < n && nxt !== null; i++) nxt = nxt.next;
    cur.next = nxt;
    cur = nxt;
  }
  return head;
}

function solve(head, m, n) {
  if (Array.isArray(head)) {
    if (head.length === 0) return [];
    const nodes = head.map((v) => new ListNode(v));
    for (let i = 0; i < nodes.length - 1; i++) nodes[i].next = nodes[i + 1];
    let cur = deleteNodesLink(nodes[0], m, n);
    const out = [];
    while (cur !== null) {
      out.push(cur.val);
      cur = cur.next;
    }
    return out;
  }
  return deleteNodesLink(head, m, n);
}

function deleteNodes(head, m, n) {
  return solve(head, m, n);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.deleteNodes = deleteNodes;
module.exports.ListNode = ListNode;
