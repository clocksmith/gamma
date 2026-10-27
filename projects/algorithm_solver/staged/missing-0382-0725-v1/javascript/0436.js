'use strict';

// 436. Find Right Interval.

function _lowerBound(a, value) {
  let lo = 0;
  let hi = a.length;
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    if (a[mid] < value) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}
function _upperBound(a, value) {
  let lo = 0;
  let hi = a.length;
  while (lo < hi) {
    const mid = Math.floor((lo + hi) / 2);
    if (a[mid] <= value) lo = mid + 1;
    else hi = mid;
  }
  return lo;
}

function solve(intervals) {
  const ordered = intervals.map((interval, index) => [interval[0], index]).sort((a, b) => a[0] - b[0]);
  const starts = ordered.map(item => item[0]);
  return intervals.map(([, end]) => {
    const index = _lowerBound(starts, end);
    return index < ordered.length ? ordered[index][1] : -1;
  });
}

const findRightInterval = solve;
class Solution {
  findRightInterval(intervals) { return solve(intervals); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findRightInterval };
