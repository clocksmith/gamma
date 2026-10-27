'use strict';

// 478. Generate Random Point in a Circle.

class Solution {
  constructor(radius, x_center, y_center) { this.radius = radius; this.x = x_center; this.y = y_center; }
  randPoint() {
    const angle = 2 * Math.PI * Math.random(), distance = this.radius * Math.sqrt(Math.random());
    return [this.x + distance * Math.cos(angle), this.y + distance * Math.sin(angle)];
  }
}

function solve(operations, args) {
  if (operations.length === 0) return [];
  const instance = new Solution(...args[0]);
  const result = [null];
  for (let i = 1; i < operations.length; i += 1) {
    const value = instance[operations[i]](...args[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

if (typeof module !== 'undefined') module.exports = { solve, Solution };
