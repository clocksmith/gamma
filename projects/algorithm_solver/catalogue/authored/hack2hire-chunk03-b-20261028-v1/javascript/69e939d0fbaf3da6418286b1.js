"use strict";
// Hack2Hire 69e939d0fbaf3da6418286b1 (Minimum Triggers to Absorb All Balls) over an INFERRED spec; qualification unknown.

function solve(balls, d) {
  const n = balls.length;
  const parent = new Int32Array(n), size = new Int32Array(n).fill(1);
  for (let i = 0; i < n; i++) parent[i] = i;
  let components = n;
  const find = (a) => {
    while (parent[a] !== a) { parent[a] = parent[parent[a]]; a = parent[a]; }
    return a;
  };
  for (const axis of [0, 1]) {
    const other = 1 - axis;
    const order = Array.from({length: n}, (_, i) => i);
    order.sort((a, b) => (balls[a][axis] - balls[b][axis]) || (balls[a][other] - balls[b][other]));
    for (let k = 0; k + 1 < n; k++) {
      const a = order[k], b = order[k + 1];
      if (balls[a][axis] === balls[b][axis] && balls[b][other] - balls[a][other] <= d) {
        let ra = find(a), rb = find(b);
        if (ra !== rb) {
          if (size[ra] < size[rb]) [ra, rb] = [rb, ra];
          parent[rb] = ra; size[ra] += size[rb]; components--;
        }
      }
    }
  }
  return components;
}

function minTriggers(balls, d) { return solve(balls, d); }

module.exports = solve;
module.exports.minTriggers = minTriggers;
