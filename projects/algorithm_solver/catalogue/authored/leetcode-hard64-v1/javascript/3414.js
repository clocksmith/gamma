'use strict';

// 3414. Maximum Score of Non-overlapping Intervals: weighted interval scheduling with bounded cardinality and explicit tie-breaking.
// O(n log n) time and O(n) auxiliary space; at most four indices per state. Inputs are preserved.
function solve(intervals) {
  const ordered = intervals.map(([start, end, weight], index) => [end, start, weight, index]);
  ordered.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2] || a[3] - b[3]);
  const n = ordered.length;
  const predecessors = new Int32Array(n);
  for (let position = 0; position < n; position += 1) {
    let left = 0;
    let right = n;
    while (left < right) {
      const middle = Math.floor((left + right) / 2);
      if (ordered[middle][0] < ordered[position][1]) left = middle + 1;
      else right = middle;
    }
    predecessors[position] = left;
  }
  function better(candidate, incumbent) {
    if (candidate[0] !== incumbent[0]) return candidate[0] > incumbent[0];
    const first = candidate[1];
    const second = incumbent[1];
    for (let index = 0; index < Math.min(first.length, second.length); index += 1) {
      if (first[index] !== second[index]) return first[index] < second[index];
    }
    return first.length < second.length;
  }
  let previous = Array.from({ length: n + 1 }, () => [0, []]);
  for (let chosen = 1; chosen <= 4; chosen += 1) {
    const current = Array.from({ length: n + 1 }, () => [0, []]);
    for (let position = 1; position <= n; position += 1) {
      const [, , weight, index] = ordered[position - 1];
      const [score, indices] = previous[predecessors[position - 1]];
      const candidate = [score + weight, [...indices, index].sort((a, b) => a - b)];
      const incumbent = current[position - 1];
      current[position] = better(candidate, incumbent) ? candidate : incumbent;
    }
    previous = current;
  }
  return previous[n][1].slice();
}

const maximumWeight = solve;
class Solution {
  maximumWeight(intervals) { return solve(intervals); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumWeight };
