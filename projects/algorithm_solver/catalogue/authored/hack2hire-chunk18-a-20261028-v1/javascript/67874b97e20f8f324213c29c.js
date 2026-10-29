"use strict";
// Hack2Hire 67874b97e20f8f324213c29c (Maximum Number of Balanced Shipments) over an INFERRED spec; qualification unknown.

function solve(weights) {
  const n = weights.length;
  const best = new Array(n + 1).fill(-1);
  best[0] = 0;
  const prefix = new Array(n + 1).fill(0);
  const stack = [];
  for (let i = 0; i < n; i++) {
    while (stack.length > 0 && weights[stack[stack.length - 1]] <= weights[i]) stack.pop();
    if (stack.length > 0 && prefix[stack[stack.length - 1]] >= 0) best[i + 1] = prefix[stack[stack.length - 1]] + 1;
    stack.push(i);
    prefix[i + 1] = Math.max(prefix[i], best[i + 1]);
  }
  return Math.max(best[n], 0);
}

function maxBalancedShipments(weights) { return solve(weights); }

module.exports = solve;
module.exports.maxBalancedShipments = maxBalancedShipments;
