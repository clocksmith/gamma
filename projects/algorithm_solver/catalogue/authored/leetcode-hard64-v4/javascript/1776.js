'use strict';

// 1776. Car Fleet II. Monotonic stack of future fleets; O(n) time and O(n) space. Inputs are preserved.

function solve(cars) {
  const answer = Array(cars.length).fill(-1);
  const stack = [];
  for (let index = cars.length - 1; index >= 0; index -= 1) {
    const [position, speed] = cars[index];
    while (stack.length > 0) {
      const front = stack[stack.length - 1];
      const [nextPosition, nextSpeed] = cars[front];
      if (speed <= nextSpeed) {
        stack.pop();
        continue;
      }
      const collision = (nextPosition - position) / (speed - nextSpeed);
      if (answer[front] < 0 || collision <= answer[front]) {
        answer[index] = collision;
        break;
      }
      stack.pop();
    }
    stack.push(index);
  }
  return answer;
}

const getCollisionTimes = solve;
class Solution {
  getCollisionTimes(cars) { return solve(cars); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getCollisionTimes };
