'use strict';

// 2517. Maximum Tastiness of Candy Basket: binary search the minimum separation with an earliest-feasible greedy selection.
// O(n log n + n log(M + 1)) time and O(n) auxiliary space, where M is the price range; inputs are read-only.
function solve(price, k) {
  const ordered = price.slice().sort((left, right) => left - right);
  let low = 0;
  let high = Math.floor((ordered[ordered.length - 1] - ordered[0]) / (k - 1));
  while (low < high) {
    const gap = Math.floor((low + high + 1) / 2);
    let selected = 1;
    let last = ordered[0];
    for (let index = 1; index < ordered.length && selected < k; index += 1) {
      if (ordered[index] - last >= gap) {
        selected += 1;
        last = ordered[index];
      }
    }
    if (selected >= k) low = gap;
    else high = gap - 1;
  }
  return low;
}

const maximumTastiness = solve;
class Solution {
  maximumTastiness(price, k) { return solve(price, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, maximumTastiness };
