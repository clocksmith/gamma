'use strict';

// 1698. Maximum Number of Events That Can Be Attended (Medium).
// Specification: https://leetcode.com/problems/maximum-number-of-events-that-can-be-attended/description/
function solve(events) {
  events = events.slice().sort((a, b) => a[0] - b[0]);
  const heap = [];
  function push(value) { heap.push(value); let i = heap.length - 1; while (i > 0) { const parent = Math.floor((i - 1) / 2); if (heap[parent] <= heap[i]) break; [heap[parent], heap[i]] = [heap[i], heap[parent]]; i = parent; } }
  function pop() { const top = heap[0]; const last = heap.pop(); if (heap.length > 0) { heap[0] = last; let i = 0; for (;;) { const left = 2 * i + 1; const right = 2 * i + 2; let smallest = i; if (left < heap.length && heap[left] < heap[smallest]) smallest = left; if (right < heap.length && heap[right] < heap[smallest]) smallest = right; if (smallest === i) break; [heap[i], heap[smallest]] = [heap[smallest], heap[i]]; i = smallest; } } return top; }
  let day = 0; let i = 0; let count = 0;
  while (i < events.length || heap.length > 0) {
    if (heap.length === 0) day = Math.max(day, events[i][0]);
    while (i < events.length && events[i][0] <= day) { push(events[i][1]); i++; }
    while (heap.length > 0 && heap[0] < day) pop();
    if (heap.length > 0) { pop(); count++; day++; }
  }
  return count;
}
const maxEvents = solve;
class Solution { maxEvents(events) { return solve(events); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxEvents };
