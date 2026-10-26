'use strict';

// 1947. Maximum Compatibility Score Sum: assign students in order using a subset of already chosen mentors.
// O(m^2 * q + m * 2^m) time and O(m^2 + 2^m) space, with m pairs and q questions; inputs are read-only.
function solve(students, mentors) {
  const count = students.length;
  const scores = Array.from({ length: count }, () => new Array(count).fill(0));
  for (let student = 0; student < count; student += 1) {
    for (let mentor = 0; mentor < count; mentor += 1) {
      for (let question = 0; question < students[student].length; question += 1) {
        if (students[student][question] === mentors[mentor][question]) scores[student][mentor] += 1;
      }
    }
  }
  const size = 1 << count;
  const cardinality = new Uint8Array(size);
  for (let mask = 1; mask < size; mask += 1) cardinality[mask] = cardinality[mask >> 1] + (mask & 1);
  const best = new Int32Array(size).fill(-1);
  best[0] = 0;
  for (let mask = 0; mask < size - 1; mask += 1) {
    const student = cardinality[mask];
    for (let mentor = 0; mentor < count; mentor += 1) {
      const bit = 1 << mentor;
      if (mask & bit) continue;
      const next = mask | bit;
      best[next] = Math.max(best[next], best[mask] + scores[student][mentor]);
    }
  }
  return best[size - 1];
}

const maxCompatibilitySum = solve;
class Solution {
  maxCompatibilitySum(students, mentors) { return solve(students, mentors); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxCompatibilitySum };
