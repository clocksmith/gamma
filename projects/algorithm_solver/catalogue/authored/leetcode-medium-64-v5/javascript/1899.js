'use strict';

// 1899. Merge Triplets to Form Target Triplet: collect target coordinates only from triplets that cannot overshoot.
// O(n) time and O(1) auxiliary space; inputs are read-only.
function solve(triplets, target) {
  const found = [false, false, false];
  for (const triplet of triplets) {
    if (triplet[0] > target[0] || triplet[1] > target[1] || triplet[2] > target[2]) continue;
    for (let index = 0; index < 3; index += 1) {
      if (triplet[index] === target[index]) found[index] = true;
    }
    if (found[0] && found[1] && found[2]) return true;
  }
  return false;
}

const mergeTriplets = solve;
class Solution {
  mergeTriplets(triplets, target) { return solve(triplets, target); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mergeTriplets };
