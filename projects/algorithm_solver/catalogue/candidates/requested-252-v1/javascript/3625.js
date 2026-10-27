/**
 * 3625. Count Number of Trapezoids II
 * Candidate source; not executed, syntax-checked, tested, or qualified.
 * Specification: https://leetcode.com/problems/count-number-of-trapezoids-ii/description/
 * Consulted specification/algorithm reference: https://github.com/doocs/leetcode/blob/f39d6eb98551c8b90713a26a70bf681494803ab9/solution/3600-3699/3625.Count%20Number%20of%20Trapezoids%20II/README_EN.md
 * Complexity: O(n^2 log C) time for normalized integer directions; O(n^2) space.
 * Inputs preserved. Integer line keys avoid floating-point slope equality. Counts fit Number for n <= 500.
 */

function solve(points) {
  const slopes = new Map(), lines = new Map();
  const midpoints = new Map(), midpointSlopes = new Map();
  function gcd(a, b) {
    while (b !== 0) { const remainder = a % b; a = b; b = remainder; }
    return a;
  }
  function increment(map, key) { map.set(key, (map.get(key) || 0) + 1); }
  let parallelPairs = 0, parallelograms = 0;
  for (let i = 0; i < points.length; i += 1) {
    const [x1, y1] = points[i];
    for (let j = 0; j < i; j += 1) {
      const [x2, y2] = points[j];
      let dx = x2 - x1, dy = y2 - y1;
      const divisor = gcd(Math.abs(dx), Math.abs(dy));
      dx /= divisor; dy /= divisor;
      if (dx < 0 || (dx === 0 && dy < 0)) { dx = -dx; dy = -dy; }
      const slope = dx + ',' + dy;
      const line = slope + ',' + (dx * y1 - dy * x1);
      const middle = (x1 + x2) + ',' + (y1 + y2);
      const middleSlope = middle + ':' + slope;
      parallelPairs += (slopes.get(slope) || 0) - (lines.get(line) || 0);
      parallelograms += (midpoints.get(middle) || 0) - (midpointSlopes.get(middleSlope) || 0);
      increment(slopes, slope); increment(lines, line);
      increment(midpoints, middle); increment(midpointSlopes, middleSlope);
    }
  }
  return parallelPairs - parallelograms;
}

function countTrapezoids(points) {
  return solve(points);
}

class Solution {
  countTrapezoids(points) {
    return solve(points);
  }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { solve, countTrapezoids, Solution };
}
