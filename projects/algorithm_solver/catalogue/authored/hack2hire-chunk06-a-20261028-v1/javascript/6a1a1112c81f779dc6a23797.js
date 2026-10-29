"use strict";
// Hack2Hire 6a1a1112c81f779dc6a23797 (Factory Network Cost Minimization, variant 2 of 3) over an INFERRED spec; qualification unknown.

function solve(costs) {
  let best1 = 0, index1 = -1, best2 = 0;
  for (const row of costs) {
    let b1 = Infinity, i1 = -1, b2 = Infinity;
    for (let j = 0; j < row.length; j++) {
      const value = row[j] + (j === index1 ? best2 : best1);
      if (value < b1) { b2 = b1; b1 = value; i1 = j; }
      else if (value < b2) b2 = value;
    }
    best1 = b1; index1 = i1; best2 = b2;
  }
  return best1 === Infinity ? -1 : best1;
}

function minimumCost(costs) { return solve(costs); }

module.exports = solve;
module.exports.minimumCost = minimumCost;
