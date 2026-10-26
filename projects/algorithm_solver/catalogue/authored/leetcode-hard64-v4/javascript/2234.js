'use strict';

// 2234. Maximum Total Beauty of the Gardens. Enumerate completed suffixes with a monotone leveling prefix; O(n log n) time and O(n) space. Inputs are preserved.

function solve(flowers, newFlowers, target, full, partial) {
  const ordered = flowers.slice().sort((a, b) => a - b);
  const size = ordered.length;
  let incomplete = size;
  while (incomplete > 0 && ordered[incomplete - 1] >= target) incomplete -= 1;
  const prefix = [0];
  for (let index = 0; index < incomplete; index += 1) prefix.push(prefix[prefix.length - 1] + ordered[index]);
  let group = incomplete;
  let remaining = newFlowers;
  let answer = (size - incomplete) * full;
  while (remaining >= 0) {
    if (incomplete === 0) return Math.max(answer, size * full);
    group = Math.min(group, incomplete);
    while (group > 1 && ordered[group - 1] * group - prefix[group] > remaining) group -= 1;
    const minimum = Math.min(target - 1, Math.floor((remaining + prefix[group]) / group));
    answer = Math.max(answer, (size - incomplete) * full + minimum * partial);
    remaining -= target - ordered[incomplete - 1];
    incomplete -= 1;
  }
  return answer;
}

const maximumBeauty = solve;
class Solution {
  maximumBeauty(flowers, newFlowers, target, full, partial) { return solve(flowers, newFlowers, target, full, partial); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumBeauty };
