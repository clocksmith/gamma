'use strict';

// 2731. Movement of Robots: treat collisions as exchanged identities and sum sorted final-position differences.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums, s, d) {
  const modulus = 1000000007;
  const positions = nums.map((value, index) => value + (s[index] === 'R' ? d : -d))
    .sort((left, right) => left - right);
  let prefix = 0;
  let result = 0;
  for (let index = 0; index < positions.length; index += 1) {
    result = (result + index * positions[index] - prefix) % modulus;
    prefix += positions[index];
  }
  return result;
}

const sumDistance = solve;
class Solution {
  sumDistance(nums, s, d) { return solve(nums, s, d); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumDistance };
