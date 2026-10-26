'use strict';

// 1755. Closest Subsequence Sum: meet-in-the-middle subset sums and binary search; O(n*2^(n/2)) time and O(2^(n/2)) space.

function solve(nums, goal) {
  const middle = Math.floor(nums.length / 2);
  function sums(start, end) {
    const result = [0];
    for (let index = start; index < end; index += 1) {
      const size = result.length;
      for (let previous = 0; previous < size; previous += 1) result.push(result[previous] + nums[index]);
    }
    return result;
  }
  const left = sums(0, middle);
  const right = sums(middle, nums.length).sort((a, b) => a - b);
  let answer = Math.abs(goal);
  for (const value of left) {
    const desired = goal - value;
    let low = 0;
    let high = right.length;
    while (low < high) {
      const center = Math.floor((low + high) / 2);
      if (right[center] < desired) low = center + 1;
      else high = center;
    }
    if (low < right.length) answer = Math.min(answer, Math.abs(desired - right[low]));
    if (low > 0) answer = Math.min(answer, Math.abs(desired - right[low - 1]));
    if (answer === 0) break;
  }
  return answer;
}

const minAbsDifference = solve;
class Solution {
  minAbsDifference(nums, goal) { return solve(nums, goal); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, minAbsDifference };
