"use strict";

function Node(val, prev, next, child) {
  this.val = val;
  this.prev = prev === undefined ? null : prev;
  this.next = next === undefined ? null : next;
  this.child = child === undefined ? null : child;
}

function fromMultilevelList(arr) {
  if (!arr || arr.length === 0) return null;
  const n = arr.length;
  let i = 0;
  const nodes = [];
  while (i < n && arr[i] !== null && arr[i] !== undefined) {
    nodes.push(new Node(arr[i], null, null, null));
    i++;
  }
  for (let j = 0; j < nodes.length - 1; j++) {
    nodes[j].next = nodes[j + 1];
    nodes[j + 1].prev = nodes[j];
  }
  let curr = nodes[0];
  i++;
  while (i < n) {
    while (i < n && (arr[i] === null || arr[i] === undefined)) {
      curr = curr.next;
      i++;
    }
    if (i >= n) break;
    const chain = [];
    while (i < n && arr[i] !== null && arr[i] !== undefined) {
      chain.push(new Node(arr[i], null, null, null));
      i++;
    }
    for (let j = 0; j < chain.length - 1; j++) {
      chain[j].next = chain[j + 1];
      chain[j + 1].prev = chain[j];
    }
    curr.child = chain[0];
    curr = chain[0];
    i++;
  }
  return nodes[0];
}

function flattenNodes(head) {
  if (!head) return null;
  const dummy = new Node(0, null, head, null);
  let prev = dummy;
  const stack = [head];
  while (stack.length > 0) {
    const curr = stack.pop();
    prev.next = curr;
    curr.prev = prev;
    if (curr.next !== null) stack.push(curr.next);
    if (curr.child !== null) {
      stack.push(curr.child);
      curr.child = null;
    }
    prev = curr;
  }
  dummy.next.prev = null;
  return dummy.next;
}

function solve(head) {
  if (Array.isArray(head)) {
    const root = fromMultilevelList(head);
    let cur = flattenNodes(root);
    const out = [];
    while (cur !== null) {
      out.push(cur.val);
      cur = cur.next;
    }
    return out;
  }
  return flattenNodes(head);
}

function flatten(head) {
  return solve(head);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.flatten = flatten;
module.exports.Node = Node;
