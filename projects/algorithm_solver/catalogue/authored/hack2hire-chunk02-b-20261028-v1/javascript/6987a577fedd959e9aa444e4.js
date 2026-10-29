"use strict";
// Original Hack2Hire 6987a577fedd959e9aa444e4 variant over an INFERRED specification; qualification unknown.
function solve(parent, input) {
  const n = parent.length, children = Array.from({length: n}, () => []);
  for (let node = 1; node < n; node++) children[parent[node]].push(node);
  const order = [0];
  for (let head = 0; head < order.length; head++) for (const c of children[order[head]]) order.push(c);
  const subtree = input.slice();
  for (let i = order.length - 1; i > 0; i--) subtree[parent[order[i]]] += subtree[order[i]];
  let best = Infinity;
  for (let node = 1; node < n; node++) best = Math.min(best, Math.abs(subtree[0] - 2 * subtree[node]));
  return best;
}
function minDrainageSplitDifference(parent, input) { return solve(parent, input); }
module.exports = solve;
module.exports.minDrainageSplitDifference = minDrainageSplitDifference;
