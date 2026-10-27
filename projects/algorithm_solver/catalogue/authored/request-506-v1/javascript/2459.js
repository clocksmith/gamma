// Original candidate. Contract: https://leetcode.com/problems/sort-array-by-moving-items-to-empty-space/
"use strict";

function solve(nums) {
  const n = nums.length;
  const blank = nums.indexOf(0);

  function cost(shift) {
    const seen = Array(n).fill(false);
    let answer = 0;
    for (let start = 0; start < n; start++) {
      if (seen[start]) continue;
      let index = start;
      let length = 0;
      let containsBlank = false;
      while (!seen[index]) {
        seen[index] = true;
        length++;
        containsBlank = containsBlank || index === blank;
        index = (nums[index] - shift + n) % n;
      }
      // Other cycles need one move to bring in the blank and one to leave.
      if (length > 1) answer += containsBlank ? length - 1 : length + 1;
    }
    return answer;
  }

  // Both 0,1,...,n-1 and 1,2,...,n-1,0 are valid final orders.
  return Math.min(cost(0), cost(1));
}

module.exports = solve;
