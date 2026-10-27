/**
 * 3893. Maximum Team Size with Overlapping Intervals
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-team-size-with-overlapping-intervals/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3800-3899/3893.Maximum%20Team%20Size%20with%20Overlapping%20Intervals/README_EN.md
 * Complexity: O(n log n) time, O(n) space.
 * Closed intervals. One central interval must meet all members; pairwise common intersection is not required. Inputs preserved.
 */

function solve(startTime, endTime) {
  const starts = startTime.slice().sort((a, b) => a - b);
  const ends = endTime.slice().sort((a, b) => a - b);
  function bound(values, target, inclusive) {
    let low = 0;
    let high = values.length;
    while (low < high) {
      const middle = Math.floor((low + high) / 2);
      if (values[middle] < target || (inclusive && values[middle] === target)) low = middle + 1;
      else high = middle;
    }
    return low;
  }
  let answer = 0;
  for (let index = 0; index < starts.length; index += 1) {
    answer = Math.max(answer, bound(starts, endTime[index], true) - bound(ends, startTime[index], false));
  }
  return answer;
}

function maximumTeamSize(startTime, endTime) {
  return solve(startTime, endTime);
}

class Solution {
  maximumTeamSize(startTime, endTime) {
    return solve(startTime, endTime);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, maximumTeamSize, Solution };
}
