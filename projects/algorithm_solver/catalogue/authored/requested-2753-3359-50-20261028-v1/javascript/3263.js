"use strict";

function solve(head) {
  if (Array.isArray(head)) return head.slice();
  const out = [];
  let cur = head;
  while (cur !== null && cur !== undefined) {
    out.push(cur.val);
    cur = cur.next;
  }
  return out;
}

function toArray(head) {
  return solve(head);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.toArray = toArray;
