'use strict';

// 502. IPO (Hard).
// Specification: https://leetcode.com/problems/ipo/description/
function solve(k, w, profits, capital) {
  const projects = profits.map((p, i) => [capital[i], p]).sort((a, b) => a[0] - b[0]);
  const heap = [];
  function push(value) {
    heap.push(value);
    let i = heap.length - 1;
    while (i > 0) {
      const parent = Math.floor((i - 1) / 2);
      if (heap[parent] >= heap[i]) break;
      [heap[parent], heap[i]] = [heap[i], heap[parent]];
      i = parent;
    }
  }
  function pop() {
    const answer = heap[0], last = heap.pop();
    if (heap.length) {
      heap[0] = last;
      let i = 0;
      while (2 * i + 1 < heap.length) {
        let child = 2 * i + 1;
        if (child + 1 < heap.length && heap[child + 1] > heap[child]) child++;
        if (heap[i] >= heap[child]) break;
        [heap[i], heap[child]] = [heap[child], heap[i]];
        i = child;
      }
    }
    return answer;
  }
  let current = w, index = 0;
  for (let step = 0; step < k; step++) {
    while (index < projects.length && projects[index][0] <= current) push(projects[index++][1]);
    if (!heap.length) break;
    current += pop();
  }
  return current;
}
const findMaximizedCapital = solve;
class Solution { findMaximizedCapital(k, w, profits, capital) { return solve(k, w, profits, capital); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaximizedCapital };
