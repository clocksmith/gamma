'use strict';

// 2966. Divide Array Into Arrays With Max Difference: group consecutive sorted values and reject any triple exceeding the spread limit.
// O(n log n) time and O(n) auxiliary space; inputs are read-only.
function solve(nums, k) {
  const ordered = nums.slice().sort((left, right) => left - right);
  const groups = [];
  for (let index = 0; index < nums.length; index += 3) {
    if (ordered[index + 2] - ordered[index] > k) return [];
    groups.push(ordered.slice(index, index + 3));
  }
  return groups;
}

const divideArray = solve;
class Solution {
  divideArray(nums, k) { return solve(nums, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, divideArray };
