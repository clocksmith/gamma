// Original candidate implementation. Contract: https://leetcode.com/problems/earliest-second-to-mark-indices-i/
"use strict";

function solve(nums, changeIndices) {
  const n = nums.length;
  const m = changeIndices.length;
  function feasible(seconds) {
    const last = Array(n).fill(-1);
    for (let time = 0; time < seconds; time++) {
      last[changeIndices[time] - 1] = time;
    }
    if (last.includes(-1)) return false;
    let free = 0;
    for (let time = 0; time < seconds; time++) {
      const index = changeIndices[time] - 1;
      if (last[index] === time) {
        if (free < nums[index]) return false;
        free -= nums[index];
      } else {
        free++;
      }
    }
    return true;
  }
  if (!feasible(m)) return -1;
  let low = 1;
  let high = m;
  while (low < high) {
    const middle = (low + high) >> 1;
    if (feasible(middle)) high = middle;
    else low = middle + 1;
  }
  return low;
}

module.exports = solve;
