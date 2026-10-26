'use strict';

// 1847. Closest Room.
// Offline size sweep with Fenwick order statistics on room IDs; O((n+q) log n + q log q) time, O(n+q) space. Inputs are preserved.

function solve(rooms, queries) {
  const ids = rooms.map(room => room[0]).sort((a, b) => a - b);
  const ranks = new Map(ids.map((value, index) => [value, index + 1]));
  const ordered = rooms.slice().sort((a, b) => b[1] - a[1]);
  const requests = queries.map((query, index) => [index, query]).sort((a, b) => b[1][1] - a[1][1]);
  const tree = Array(ids.length + 1).fill(0);
  function prefix(index) { let sum = 0; for (; index > 0; index -= index & -index) sum += tree[index]; return sum; }
  function select(order) {
    let index = 0, step = 1;
    while (step * 2 <= ids.length) step *= 2;
    for (; step > 0; step = Math.floor(step / 2)) {
      const next = index + step;
      if (next < tree.length && tree[next] < order) { order -= tree[next]; index = next; }
    }
    return ids[index];
  }
  const answers = Array(queries.length).fill(-1);
  let admitted = 0;
  for (const [queryIndex, [preferred, minimumSize]] of requests) {
    while (admitted < ordered.length && ordered[admitted][1] >= minimumSize) {
      for (let i = ranks.get(ordered[admitted][0]); i < tree.length; i += i & -i) tree[i] += 1;
      admitted += 1;
    }
    if (admitted === 0) continue;
    let low = 0, high = ids.length;
    while (low < high) {
      const mid = Math.floor((low + high) / 2);
      if (ids[mid] <= preferred) low = mid + 1; else high = mid;
    }
    const before = prefix(low), candidates = [];
    if (before > 0) candidates.push(select(before));
    if (before < admitted) candidates.push(select(before + 1));
    candidates.sort((a, b) => Math.abs(a - preferred) - Math.abs(b - preferred) || a - b);
    answers[queryIndex] = candidates[0];
  }
  return answers;
}

const closestRoom = solve;
class Solution {
  closestRoom(rooms, queries) { return solve(rooms, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, closestRoom };
