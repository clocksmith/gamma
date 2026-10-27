/**
 * 4057. Number of Intersecting Interval Pairs II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/number-of-intersecting-interval-pairs-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/4000-4099/4057.Number%20of%20Intersecting%20Interval%20Pairs%20II/README_EN.md
 * Complexity: O(n log n) time, O(n) space.
 * Closed endpoints intersect. Each strictly disjoint pair is subtracted once. Inputs preserved.
 */

function solve(intervals) {
  const starts=intervals.map(x=>x[0]).sort((a,b)=>a-b),ends=intervals.map(x=>x[1]).sort((a,b)=>a-b);
  const n=intervals.length;let answer=n*(n-1)/2,finished=0;
  for(const start of starts){while(finished<n && ends[finished]<start)finished++;answer-=finished;}
  return answer;
}

function countIntersectingIntervals(intervals) {
  return solve(intervals);
}

class Solution {
  countIntersectingIntervals(intervals) {
    return solve(intervals);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, countIntersectingIntervals, Solution };
}
