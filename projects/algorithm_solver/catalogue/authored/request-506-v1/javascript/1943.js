// Original candidate implementation. Contract: https://leetcode.com/problems/describe-the-painting/
"use strict";

function solve(segments) {
  const events = new Map();
  for (const [left, right, color] of segments) {
    events.set(left, (events.get(left) || 0) + color);
    events.set(right, (events.get(right) || 0) - color);
  }
  const answer = [];
  let previous = null;
  let total = 0;
  for (const position of [...events.keys()].sort((a, b) => a - b)) {
    // Preserve color-set boundaries, even when adjacent sums coincide.
    if (previous !== null && total) answer.push([previous, position, total]);
    total += events.get(position);
    previous = position;
  }
  return answer;
}

module.exports = solve;
