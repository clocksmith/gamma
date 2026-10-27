/**
 * 3661. Maximum Walls Destroyed by Robots
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/maximum-walls-destroyed-by-robots/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3661.Maximum%20Walls%20Destroyed%20by%20Robots/README_EN.md
 * Complexity: O(n log n + m log m + n log m) time; O(n+m) space.
 * Inputs preserved. Robot-position walls counted once independently; gap DP counts unions without double counting.
 */

function solve(robots, distance, walls) {
  const machines = robots.map((position, i) => [position, distance[i]]).sort((a, b) => a[0] - b[0]);
  const positions = new Set(robots);
  const remaining = walls.filter(wall => !positions.has(wall)).sort((a, b) => a - b);
  const fixed = walls.length - remaining.length;
  function lowerBound(value) {
    let left = 0, right = remaining.length;
    while (left < right) { const middle = Math.floor((left + right) / 2); if (remaining[middle] < value) left = middle + 1; else right = middle; }
    return left;
  }
  function count(left, right) { return left > right ? 0 : lowerBound(right + 1) - lowerBound(left); }
  let leftScore = count(machines[0][0] - machines[0][1], machines[0][0] - 1), rightScore = 0;
  for (let i = 0; i + 1 < machines.length; i += 1) {
    const [left, leftReach] = machines[i], [right, rightReach] = machines[i + 1];
    const rightEnd = Math.min(right - 1, left + leftReach);
    const leftStart = Math.max(left + 1, right - rightReach);
    const fromLeft = count(left + 1, rightEnd), fromRight = count(leftStart, right - 1);
    const overlap = count(leftStart, rightEnd);
    const nextLeft = Math.max(leftScore + fromRight, rightScore + fromLeft + fromRight - overlap);
    const nextRight = Math.max(leftScore, rightScore + fromLeft);
    leftScore = nextLeft; rightScore = nextRight;
  }
  const [last, reach] = machines[machines.length - 1];
  return fixed + Math.max(leftScore, rightScore + count(last + 1, last + reach));
}

function maxWalls(robots, distance, walls) {
  return solve(robots, distance, walls);
}

class Solution {
  maxWalls(robots, distance, walls) {
    return solve(robots, distance, walls);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, maxWalls, Solution };
}
