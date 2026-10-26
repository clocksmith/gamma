'use strict';

// 3886. Sum of Sortable Integers.
// O(n*tau(n) + sqrt(n)) time and O(tau(n)) space; each block must have at most one cyclic descent and ordered value ranges.
function solve(nums) {
  const n = nums.length;
  const divisors = [];
  for (let value = 1; value * value <= n; value += 1) {
    if (n % value === 0) {
      divisors.push(value);
      if (value * value !== n) divisors.push(n / value);
    }
  }
  let answer = 0;
  for (const width of divisors) {
    let previousMax = 0;
    let possible = true;
    for (let start = 0; start < n; start += width) {
      const end = start + width;
      let minimum = nums[start];
      let maximum = nums[start];
      let descents = Number(nums[end - 1] > nums[start]);
      for (let index = start + 1; index < end; index += 1) {
        minimum = Math.min(minimum, nums[index]);
        maximum = Math.max(maximum, nums[index]);
        if (nums[index - 1] > nums[index]) descents += 1;
      }
      if (descents > 1 || minimum < previousMax) {
        possible = false;
        break;
      }
      previousMax = maximum;
    }
    if (possible) answer += width;
  }
  return answer;
}

const sumOfSortableIntegers = solve;
class Solution {
  sumOfSortableIntegers(nums) { return solve(nums); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, sumOfSortableIntegers };
