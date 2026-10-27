'use strict';

// 475. Heaters.

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

function solve(houses, heaters) {
  const ordered = heaters.slice().sort((a, b) => a - b);
  let answer = 0;
  for (const house of houses) {
    const index = _lowerBound(ordered, house);
    const left = index > 0 ? house - ordered[index - 1] : Infinity;
    const right = index < ordered.length ? ordered[index] - house : Infinity;
    answer = Math.max(answer, Math.min(left, right));
  }
  return answer;
}

const findRadius = solve;
class Solution {
  findRadius(houses, heaters) { return solve(houses, heaters); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findRadius };
