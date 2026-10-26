'use strict';

// 2001. Number of Pairs of Interchangeable Rectangles: count matching reduced integer width-to-height ratios.
// O(n * log(M + 1)) expected time and O(n) auxiliary space, with M the largest dimension; inputs are read-only.
function solve(rectangles) {
  const counts = new Map();
  let result = 0;
  for (const [width, height] of rectangles) {
    let left = width;
    let right = height;
    while (right !== 0) [left, right] = [right, left % right];
    const key = `${width / left}:${height / left}`;
    const previous = counts.get(key) || 0;
    result += previous;
    counts.set(key, previous + 1);
  }
  return result;
}

const interchangeableRectangles = solve;
class Solution {
  interchangeableRectangles(rectangles) { return solve(rectangles); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, interchangeableRectangles };
