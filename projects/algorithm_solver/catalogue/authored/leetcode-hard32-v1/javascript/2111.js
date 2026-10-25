'use strict';

// 2111. Minimum Operations to Make the Array K-Increasing.
// O(n*log(1+n/k)) time, O(ceil(n/k)) space. Upper bound allows equal values in the LNDS.
function solve(arr, k) {
  let answer = 0;
  for (let start = 0; start < k; start += 1) {
    const tails = [];
    let count = 0;
    for (let index = start; index < arr.length; index += k) {
      const value = arr[index];
      let low = 0;
      let high = tails.length;
      while (low < high) {
        const middle = Math.floor((low + high) / 2);
        if (tails[middle] <= value) low = middle + 1;
        else high = middle;
      }
      if (low === tails.length) tails.push(value);
      else tails[low] = value;
      count += 1;
    }
    answer += count - tails.length;
  }
  return answer;
}

const kIncreasing = solve;
class Solution {
  kIncreasing(arr, k) { return solve(arr, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kIncreasing };
