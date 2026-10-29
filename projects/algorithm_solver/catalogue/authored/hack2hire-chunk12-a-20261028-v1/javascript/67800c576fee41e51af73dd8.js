"use strict";
// Hack2Hire 67800c576fee41e51af73dd8 (Max Consecutive ON Servers) over an INFERRED spec; qualification unknown.

function solve(states, k) {
  let left = 0, blocks = 0, best = 0;
  for (let right = 0; right < states.length; right++) {
    if (states[right] === "0" && (right === left || states[right - 1] === "1")) blocks++;
    while (blocks > k) {
      if (states[left] === "0" && !(left + 1 <= right && states[left + 1] === "0")) blocks--;
      left++;
    }
    if (right - left + 1 > best) best = right - left + 1;
  }
  return best;
}

function maxConsecutiveOn(states, k) { return solve(states, k); }

module.exports = solve;
module.exports.maxConsecutiveOn = maxConsecutiveOn;
