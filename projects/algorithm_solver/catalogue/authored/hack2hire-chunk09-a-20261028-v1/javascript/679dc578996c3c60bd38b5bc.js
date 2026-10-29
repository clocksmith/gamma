"use strict";
// Hack2Hire 679dc578996c3c60bd38b5bc (Asteroid Collision - Different Speed) over an INFERRED spec; qualification unknown.

function solve(masses, speeds) {
  const stack = []; // indices of survivors so far
  for (let i = 0; i < masses.length; i++) {
    if (speeds[i] > 0) { stack.push(i); continue; }
    const power = masses[i] * -speeds[i];
    let alive = true;
    while (stack.length && speeds[stack[stack.length - 1]] > 0) {
      const t = stack[stack.length - 1];
      const other = masses[t] * speeds[t];
      if (other < power) { stack.pop(); continue; }
      if (other === power) stack.pop();
      alive = false;
      break;
    }
    if (alive) stack.push(i);
  }
  return stack.map((i) => [masses[i], speeds[i]]);
}

function asteroidCollision(masses, speeds) { return solve(masses, speeds); }

module.exports = solve;
module.exports.asteroidCollision = asteroidCollision;
