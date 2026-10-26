'use strict';

// 1499. Max Value of Equation: monotonic deque for y-x inside the x-distance window; O(n) time and O(n) space.

function solve(points, k) {
  const queue = [];
  let head = 0;
  let answer = -Infinity;
  for (let index = 0; index < points.length; index += 1) {
    const [x, y] = points[index];
    while (head < queue.length && x - points[queue[head]][0] > k) head += 1;
    if (head < queue.length) {
      const [previousX, previousY] = points[queue[head]];
      answer = Math.max(answer, x + y + previousY - previousX);
    }
    const value = y - x;
    while (queue.length > head) {
      const [previousX, previousY] = points[queue[queue.length - 1]];
      if (previousY - previousX > value) break;
      queue.pop();
    }
    queue.push(index);
  }
  return answer;
}

const findMaxValueOfEquation = solve;
class Solution {
  findMaxValueOfEquation(points, k) { return solve(points, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findMaxValueOfEquation };
