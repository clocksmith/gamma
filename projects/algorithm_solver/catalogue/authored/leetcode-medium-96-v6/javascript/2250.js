'use strict';

// 2250. Count Number of Rectangles Containing Each Point: group rectangle widths by the bounded height and binary search qualifying widths.
// O(n log n + q H log(n + 1)) time and O(n + q + H) space with H = 100; inputs are read-only.
function solve(rectangles, points) {
  const widths = Array.from({ length: 101 }, () => []);
  for (const [width, height] of rectangles) widths[height].push(width);
  for (const group of widths) group.sort((left, right) => left - right);
  return points.map(([x, y]) => {
    let count = 0;
    for (let height = y; height <= 100; height += 1) {
      const group = widths[height];
      let low = 0;
      let high = group.length;
      while (low < high) {
        const middle = Math.floor((low + high) / 2);
        if (group[middle] < x) low = middle + 1;
        else high = middle;
      }
      count += group.length - low;
    }
    return count;
  });
}

const countRectangles = solve;
class Solution {
  countRectangles(rectangles, points) { return solve(rectangles, points); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, countRectangles };
