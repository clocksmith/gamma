/**
 * 4023. Elevator Requests II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/elevator-requests-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4023.Elevator%20Requests%20II/README_EN.md
 * Complexity: O(q^2) time, O(q) space.
 * Served floors form an interval containing start. Each expansion charges distance times outstanding requests. Start is a zero-penalty dummy if not requested; distinct requested floors only. Inputs preserved; native method unconfirmed.
 */

function solve(n, start, requests) {
  const points = Array.from(new Set([...requests, start])).sort((a, b) => a - b), size = points.length, origin = points.indexOf(start);
  let left = new Float64Array(size).fill(Infinity), right = new Float64Array(size).fill(Infinity);
  left[origin] = right[origin] = 0;
  for (let length = 1; length < size; length++) {
    const nextLeft = new Float64Array(size).fill(Infinity), nextRight = new Float64Array(size).fill(Infinity), waiting = size - length;
    for (let lo = Math.max(0, origin - length + 1); lo <= Math.min(origin, size - length); lo++) {
      const hi = lo + length - 1;
      if (lo > 0) nextLeft[lo - 1] = Math.min(nextLeft[lo - 1], left[lo] + (points[lo] - points[lo - 1]) * waiting, right[lo] + (points[hi] - points[lo - 1]) * waiting);
      if (hi + 1 < size) nextRight[lo] = Math.min(nextRight[lo], left[lo] + (points[hi + 1] - points[lo]) * waiting, right[lo] + (points[hi + 1] - points[hi]) * waiting);
    }
    left = nextLeft; right = nextRight;
  }
  return Math.min(left[0], right[0]);
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve };
}
