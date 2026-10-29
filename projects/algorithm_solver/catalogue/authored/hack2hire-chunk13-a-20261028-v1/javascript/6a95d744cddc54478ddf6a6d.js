"use strict";
// Hack2Hire 6a95d744cddc54478ddf6a6d (Optimal Team Selection) over an INFERRED spec; qualification unknown.

function feasible(lowerSkill, higherSkill, k) {
  let taken = 0;
  for (let i = 0; i < lowerSkill.length; i++) {
    if (taken <= lowerSkill[i] && k - 1 - taken <= higherSkill[i]) {
      taken++;
      if (taken === k) return true;
    }
  }
  return false;
}

function solve(lowerSkill, higherSkill) {
  let lo = 1, hi = lowerSkill.length; // a single developer is always a valid team
  while (lo < hi) {
    const mid = Math.floor((lo + hi + 1) / 2);
    if (feasible(lowerSkill, higherSkill, mid)) lo = mid; else hi = mid - 1;
  }
  return lo;
}

function maxTeamSize(lowerSkill, higherSkill) { return solve(lowerSkill, higherSkill); }

module.exports = solve;
module.exports.maxTeamSize = maxTeamSize;
