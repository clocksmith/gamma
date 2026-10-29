"use strict";
// Hack2Hire 68f5af31a269f53ea0eff8a0 (Highest Scoring Movie Group) over an INFERRED spec; qualification unknown.

// Binary min-heap helpers over a plain array.
function heapPush(heap, value) {
  heap.push(value);
  let i = heap.length - 1;
  while (i > 0) {
    const parent = (i - 1) >> 1;
    if (heap[parent] <= heap[i]) break;
    [heap[parent], heap[i]] = [heap[i], heap[parent]];
    i = parent;
  }
}

function heapPop(heap) {
  const top = heap[0];
  const last = heap.pop();
  if (heap.length > 0) {
    heap[0] = last;
    let i = 0;
    for (;;) {
      const l = 2 * i + 1, r = l + 1;
      let s = i;
      if (l < heap.length && heap[l] < heap[s]) s = l;
      if (r < heap.length && heap[r] < heap[s]) s = r;
      if (s === i) break;
      [heap[s], heap[i]] = [heap[i], heap[s]];
      i = s;
    }
  }
  return top;
}

function solve(similarityScores, groups, k) {
  let bestIndex = -1;
  let bestTotal = -1;
  for (let index = 0; index < groups.length; index++) {
    const heap = [];
    for (const movie of groups[index]) {
      heapPush(heap, similarityScores[movie]);
      if (heap.length > k) heapPop(heap);
    }
    let total = 0;
    for (const v of heap) total += v;
    if (total > bestTotal) {
      bestTotal = total;
      bestIndex = index;
    }
  }
  return bestIndex;
}

function findHighestScoringGroup(similarityScores, groups, k) { return solve(similarityScores, groups, k); }

module.exports = solve;
module.exports.findHighestScoringGroup = findHighestScoringGroup;
