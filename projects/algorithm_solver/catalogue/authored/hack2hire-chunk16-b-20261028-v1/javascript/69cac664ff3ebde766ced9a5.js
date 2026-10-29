"use strict";
// Hack2Hire 69cac664ff3ebde766ced9a5 (Minimum Absolute Difference Pairs) over an INFERRED spec; qualification unknown.

function solve(latencies) {
  const values = Float64Array.from(latencies).sort();
  let best = Infinity;
  for (let i = 1; i < values.length; i++) if (values[i] - values[i - 1] < best) best = values[i] - values[i - 1];
  const out = [];
  for (let i = 1; i < values.length; i++) if (values[i] - values[i - 1] === best) out.push([values[i - 1], values[i]]);
  return out;
}

function minimumAbsDifference(latencies) { return solve(latencies); }

module.exports = solve;
module.exports.minimumAbsDifference = minimumAbsDifference;
