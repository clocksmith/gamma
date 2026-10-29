"use strict";
// Hack2Hire 6a1e2e688b879849ebc1089e (Obstacle Placement and Block Check) over an INFERRED spec; qualification unknown.

function lowerBound(a, x) {
  let lo = 0, hi = a.length;
  while (lo < hi) { const mid = (lo + hi) >> 1; if (a[mid] < x) lo = mid + 1; else hi = mid; }
  return lo;
}

function solve(operations) {
  const coords = [...new Set(operations.filter((op) => op[0] === 1).map((op) => op[1]))].sort((a, b) => a - b);
  const m = coords.length;
  const tree = new Array(m + 1).fill(0); // Fenwick tree of placed obstacles over the compressed positions
  const placed = new Array(m).fill(false);
  const prefix = (i) => { let total = 0; while (i > 0) { total += tree[i]; i -= i & -i; } return total; };
  const out = [];
  for (const op of operations) {
    if (op[0] === 1) {
      let k = lowerBound(coords, op[1]);
      if (!placed[k]) {
        placed[k] = true;
        for (k += 1; k <= m; k += k & -k) tree[k] += 1;
      }
    } else {
      const x = op[1], size = op[2];
      const inside = prefix(lowerBound(coords, x)) - prefix(lowerBound(coords, x - size));
      out.push(inside === 0 ? "1" : "0");
    }
  }
  return out.join("");
}

function processOperations(operations) { return solve(operations); }

module.exports = solve;
module.exports.processOperations = processOperations;
