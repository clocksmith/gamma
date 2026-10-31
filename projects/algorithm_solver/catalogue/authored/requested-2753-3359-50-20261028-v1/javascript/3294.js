"use strict";

function solve(node) {
  if (Array.isArray(node)) return node.slice();
  let cur = node;
  while (cur !== null && cur !== undefined && cur.prev !== null && cur.prev !== undefined) {
    cur = cur.prev;
  }
  const out = [];
  while (cur !== null && cur !== undefined) {
    out.push(cur.val);
    cur = cur.next;
  }
  return out;
}

function toArray(node) {
  return solve(node);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.toArray = toArray;
