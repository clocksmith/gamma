'use strict';

// 735. Asteroid Collision (Medium).
// Specification: https://leetcode.com/problems/asteroid-collision/description/
function solve(asteroids) {
  const stack = [];
  for (const value of asteroids) {
    let alive = true;
    while (alive && value < 0 && stack.length > 0 && stack[stack.length - 1] > 0) {
      const top = stack[stack.length - 1];
      if (top < -value) stack.pop();
      else if (top === -value) { stack.pop(); alive = false; }
      else alive = false;
    }
    if (alive) stack.push(value);
  }
  return stack;
}
const asteroidCollision = solve;
class Solution { asteroidCollision(asteroids) { return solve(asteroids); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, asteroidCollision };
