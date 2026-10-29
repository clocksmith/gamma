"use strict";
// Hack2Hire 6a949604cddc54478ddf5f33 (Maximize Deployment Score) over an INFERRED spec; qualification unknown.

function solve(difficulty) {
  const s = difficulty.slice().sort((a, b) => a - b), n = s.length;
  return (s[n - 1] - s[0]) + Math.max(s[n - 2] - s[0], s[n - 1] - s[1]);
}

function maxDeploymentScore(difficulty) { return solve(difficulty); }

module.exports = solve;
module.exports.maxDeploymentScore = maxDeploymentScore;
