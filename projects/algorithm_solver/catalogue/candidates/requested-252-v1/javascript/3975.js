/**
 * 3975. Filter Occupied Intervals
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/filter-occupied-intervals/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3975.Filter%20Occupied%20Intervals/README_EN.md
 * Complexity: O(n log n) time, O(n) space.
 * Inclusive integer intervals; touching intervals merge. Remove free points rather than retaining the intersection. Inputs and row objects preserved.
 */

function solve(occupiedIntervals, freeStart, freeEnd) {
  const ordered = occupiedIntervals.map(pair => pair.slice()).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const merged = [];
  for (const [start, end] of ordered) {
    const last = merged[merged.length - 1];
    if (last && start <= last[1] + 1) last[1] = Math.max(last[1], end);
    else merged.push([start, end]);
  }
  const answer = [];
  for (const [start, end] of merged) {
    if (end < freeStart || start > freeEnd) answer.push([start, end]);
    else {
      if (start < freeStart) answer.push([start, freeStart - 1]);
      if (end > freeEnd) answer.push([freeEnd + 1, end]);
    }
  }
  return answer;
}

function filterOccupiedIntervals(occupiedIntervals, freeStart, freeEnd) {
  return solve(occupiedIntervals, freeStart, freeEnd);
}

class Solution {
  filterOccupiedIntervals(occupiedIntervals, freeStart, freeEnd) {
    return solve(occupiedIntervals, freeStart, freeEnd);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, filterOccupiedIntervals, Solution };
}
