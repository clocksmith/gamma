/**
 * 3961. Maximize Sum of Device Ratings
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximize-sum-of-device-ratings/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3900-3999/3961.Maximize%20Sum%20of%20Device%20Ratings/README_EN.md
 * Complexity: O(total units) time, O(1) auxiliary space.
 * One transfer maximum per source; the lowest-second-minimum device receives all discarded minima. Single-unit devices cannot improve by transfers. Inputs preserved.
 */

function solve(units) {
  if (units[0].length === 1) return units.reduce((sum, row) => sum + row[0], 0);
  let smallest = Infinity;
  let smallestSecond = Infinity;
  let total = 0;
  for (const row of units) {
    let first = Infinity;
    let second = Infinity;
    for (const value of row) {
      if (value < first) { second = first; first = value; }
      else if (value < second) second = value;
    }
    smallest = Math.min(smallest, first);
    smallestSecond = Math.min(smallestSecond, second);
    total += second;
  }
  return total - smallestSecond + smallest;
}

function maxRatings(units) {
  return solve(units);
}

class Solution {
  maxRatings(units) {
    return solve(units);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, maxRatings, Solution };
}
