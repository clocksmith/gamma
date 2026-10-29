"use strict";
// Hack2Hire 67fa954aba41b3368f4e5852 (Random User Pairing, variant 2 of 2) over an INFERRED spec; qualification unknown.

// max-heap of [unpaired count, group name]: larger count first, then smaller name
const above = (a, b) => (a[0] !== b[0] ? a[0] > b[0] : a[1] < b[1]);

function siftDown(heap, i) {
  const entry = heap[i], n = heap.length;
  for (;;) {
    const l = 2 * i + 1, r = l + 1;
    let child = l;
    if (l >= n) break;
    if (r < n && above(heap[r], heap[l])) child = r;
    if (!above(heap[child], entry)) break;
    heap[i] = heap[child]; i = child;
  }
  heap[i] = entry;
}

function push(heap, entry) {
  let i = heap.length;
  heap.push(entry);
  while (i > 0) {
    const up = (i - 1) >> 1;
    if (!above(entry, heap[up])) break;
    heap[i] = heap[up]; i = up;
  }
  heap[i] = entry;
}

function pop(heap) {
  const root = heap[0], last = heap.pop();
  if (heap.length) { heap[0] = last; siftDown(heap, 0); }
  return root;
}

function solve(users) {
  const members = new Map();
  for (const [name, group] of users) {
    let names = members.get(group);
    if (names === undefined) { names = []; members.set(group, names); }
    names.push(name);
  }
  const heap = [];
  for (const [group, names] of members) heap.push([names.length, group, names, 0]);
  for (let i = (heap.length >> 1) - 1; i >= 0; i--) siftDown(heap, i);
  const pairs = [];
  while (heap.length >= 2) {
    const a = pop(heap), b = pop(heap);
    pairs.push([a[2][a[3]], b[2][b[3]]]);
    if (a[0] > 1) push(heap, [a[0] - 1, a[1], a[2], a[3] + 1]);
    if (b[0] > 1) push(heap, [b[0] - 1, b[1], b[2], b[3] + 1]);
  }
  return pairs;
}

function pairAcrossGroups(users) { return solve(users); }

module.exports = solve;
module.exports.pairAcrossGroups = pairAcrossGroups;
