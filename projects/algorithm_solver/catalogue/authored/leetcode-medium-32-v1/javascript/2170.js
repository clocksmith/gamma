'use strict';

// 2170. Minimum Operations to Make the Array Alternating: keep the best distinct values for the two index parities.
// O(n) expected time and O(n) auxiliary space; inputs are read-only.
function solve(nums) {
  const counts = [new Map(), new Map()];
  for (let index = 0; index < nums.length; index += 1) {
    const group = counts[index % 2];
    group.set(nums[index], (group.get(nums[index]) || 0) + 1);
  }

  function topTwo(group) {
    let first = [null, 0];
    let second = [null, 0];
    for (const [value, count] of group) {
      if (count > first[1]) {
        second = first;
        first = [value, count];
      } else if (count > second[1]) {
        second = [value, count];
      }
    }
    return [first, second];
  }

  const [evenFirst, evenSecond] = topTwo(counts[0]);
  const [oddFirst, oddSecond] = topTwo(counts[1]);
  const kept = evenFirst[0] !== oddFirst[0]
    ? evenFirst[1] + oddFirst[1]
    : Math.max(evenFirst[1] + oddSecond[1], evenSecond[1] + oddFirst[1]);
  return nums.length - kept;
}

const minimumOperations = solve;
class Solution {
  minimumOperations(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minimumOperations };
