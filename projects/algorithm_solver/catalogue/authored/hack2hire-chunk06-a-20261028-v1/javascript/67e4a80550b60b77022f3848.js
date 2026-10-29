"use strict";
// Hack2Hire 67e4a80550b60b77022f3848 (Find Middle Course, variant 1 of 2) over an INFERRED spec; qualification unknown.

function solve(pairs) {
  const following = new Map(), courses = new Set();
  for (const [p, c] of pairs) { following.set(p, c); courses.add(c); }
  let current = null;
  for (const [p] of pairs) if (!courses.has(p)) { current = p; break; }
  for (let k = 0; k < pairs.length / 2; k++) current = following.get(current);
  return current;
}

function findMiddleCourse(pairs) { return solve(pairs); }

module.exports = solve;
module.exports.findMiddleCourse = findMiddleCourse;
