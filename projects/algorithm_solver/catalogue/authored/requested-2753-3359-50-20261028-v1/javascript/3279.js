"use strict";

function solve(height, positions, directions) {
  const period = 2 * height;
  const delta = new Int32Array(period + 2);
  let cur = 0;
  let slope = 0;
  for (let i = 0; i < positions.length; i++) {
    const p = positions[i];
    cur += p;
    let d = directions[i];
    if (p === 0) d = "U";
    else if (p === height) d = "D";
    if (d === "U") {
      slope += 1;
      const t1 = height - p;
      const t2 = t1 + height;
      delta[t1] -= 2;
      delta[t2] += 2;
    } else {
      slope -= 1;
      const t1 = p;
      const t2 = t1 + height;
      delta[t1] += 2;
      delta[t2] -= 2;
    }
  }
  let best = cur;
  for (let t = 1; t <= period; t++) {
    cur += slope;
    if (cur > best) best = cur;
    slope += delta[t];
  }
  return best;
}

function maxArea(height, positions, directions) {
  return solve(height, positions, directions);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.maxArea = maxArea;
