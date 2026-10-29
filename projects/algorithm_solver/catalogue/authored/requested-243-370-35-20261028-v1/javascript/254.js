"use strict";

function solve(n) {
  const res = [];
  const path = [];
  function dfs(rem, start) {
    for (let d = start; d * d <= rem; d++) {
      if (rem % d === 0) {
        const q = Math.floor(rem / d);
        res.push(path.concat([d, q]));
        path.push(d);
        dfs(q, d);
        path.pop();
      }
    }
  }
  dfs(n, 2);
  return res;
}

function getFactors(n) {
  return solve(n);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.getFactors = getFactors;
