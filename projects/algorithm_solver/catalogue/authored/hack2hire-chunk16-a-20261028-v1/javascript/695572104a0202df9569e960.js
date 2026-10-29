"use strict";
// Hack2Hire 695572104a0202df9569e960 (Merge JSON Event Logs) over an INFERRED spec; qualification unknown.

function less(a, b) {
  if (a[0] !== b[0]) return a[0] < b[0];
  if (a[1] !== b[1]) return a[1] < b[1];
  return a[2] < b[2];
}

function siftDown(heap, i) {
  for (;;) {
    const l = 2 * i + 1, r = l + 1;
    let m = i;
    if (l < heap.length && less(heap[l], heap[m])) m = l;
    if (r < heap.length && less(heap[r], heap[m])) m = r;
    if (m === i) return;
    const t = heap[i]; heap[i] = heap[m]; heap[m] = t;
    i = m;
  }
}

function solve(logs) {
  const heap = [];
  for (const server of Object.keys(logs)) {
    const events = logs[server];
    if (events.length) heap.push([events[0].time, server, 0]);
  }
  for (let i = (heap.length >> 1) - 1; i >= 0; i--) siftDown(heap, i);
  const out = [];
  while (heap.length) {
    const [, server, position] = heap[0];
    const events = logs[server];
    const event = events[position];
    const merged = {serverId: server, time: event.time, type: event.type};
    if (Object.prototype.hasOwnProperty.call(event, 'target')) merged.target = event.target;
    out.push(merged);
    if (position + 1 < events.length) heap[0] = [events[position + 1].time, server, position + 1];
    else {
      const last = heap.pop();
      if (heap.length) heap[0] = last;
    }
    if (heap.length) siftDown(heap, 0);
  }
  return out;
}

function mergeEventLogs(logs) { return solve(logs); }

module.exports = solve;
module.exports.mergeEventLogs = mergeEventLogs;
