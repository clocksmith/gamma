"use strict";
// Hack2Hire 68e870c780f69c7a0170688c (Subset Sum Target) over an INFERRED spec; qualification unknown.

function solve(nums, target) {
  const mask = (1n << BigInt(target + 1)) - 1n;
  const bit = 1n << BigInt(target);
  let reach = 1n;
  for (const value of nums) {
    reach = (reach | (reach << BigInt(value))) & mask;
    if (reach & bit) return true;
  }
  return (reach & bit) !== 0n;
}

function canReachTarget(nums, target) { return solve(nums, target); }

module.exports = solve;
module.exports.canReachTarget = canReachTarget;
