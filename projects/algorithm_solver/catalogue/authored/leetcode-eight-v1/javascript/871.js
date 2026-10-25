'use strict';

// Self-contained max heap; O(n log n) time and O(n) space, without mutation.
function solve(target, startFuel, stations) {
  const heap = [];
  function push(value) {
    let child = heap.length;
    heap.push(value);
    while (child > 0) {
      const parent = Math.floor((child - 1) / 2);
      if (heap[parent] >= value) break;
      heap[child] = heap[parent];
      child = parent;
    }
    heap[child] = value;
  }
  function pop() {
    const result = heap[0];
    const value = heap.pop();
    if (heap.length === 0) return result;
    let parent = 0;
    while (parent * 2 + 1 < heap.length) {
      let child = parent * 2 + 1;
      if (child + 1 < heap.length && heap[child + 1] > heap[child]) child += 1;
      if (heap[child] <= value) break;
      heap[parent] = heap[child];
      parent = child;
    }
    heap[parent] = value;
    return result;
  }
  let reachable = startFuel;
  let nextStation = 0;
  let stops = 0;
  while (reachable < target) {
    while (nextStation < stations.length && stations[nextStation][0] <= reachable) {
      push(stations[nextStation][1]);
      nextStation += 1;
    }
    if (heap.length === 0) return -1;
    reachable += pop();
    stops += 1;
  }
  return stops;
}

const minRefuelStops = solve;
class Solution {
  minRefuelStops(target, startFuel, stations) { return solve(target, startFuel, stations); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minRefuelStops };
