'use strict';

// 1353. Maximum Number of Events That Can Be Attended: attend the available event with the earliest ending day.
// O(n log(n + 1)) time and O(n) auxiliary space; inputs are read-only.
function solve(events) {
  const ordered = events.slice().sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const heap = [];
  function push(value) {
    let index = heap.length;
    heap.push(value);
    while (index > 0) {
      const parent = Math.floor((index - 1) / 2);
      if (heap[parent] <= value) break;
      heap[index] = heap[parent];
      index = parent;
    }
    heap[index] = value;
  }
  function pop() {
    const result = heap[0];
    const value = heap.pop();
    if (!heap.length) return result;
    let index = 0;
    while (2 * index + 1 < heap.length) {
      let child = 2 * index + 1;
      if (child + 1 < heap.length && heap[child + 1] < heap[child]) child += 1;
      if (heap[child] >= value) break;
      heap[index] = heap[child];
      index = child;
    }
    heap[index] = value;
    return result;
  }
  let index = 0;
  let day = 0;
  let attended = 0;
  while (index < ordered.length || heap.length) {
    if (!heap.length) day = ordered[index][0];
    while (index < ordered.length && ordered[index][0] <= day) {
      push(ordered[index][1]);
      index += 1;
    }
    while (heap.length && heap[0] < day) pop();
    if (heap.length) {
      pop();
      attended += 1;
      day += 1;
    }
  }
  return attended;
}

const maxEvents = solve;
class Solution {
  maxEvents(events) { return solve(events); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxEvents };
