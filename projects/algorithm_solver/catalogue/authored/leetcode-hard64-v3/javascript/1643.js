'use strict';

// 1643. Kth Smallest Instructions: binomial unranking with H before V; O((rows+columns)^2) time and space.

function solve(destination, k) {
  let [vertical, horizontal] = destination;
  const total = vertical + horizontal;
  const choose = [[1]];
  for (let length = 1; length <= total; length += 1) {
    const row = Array(length + 1).fill(1);
    for (let count = 1; count < length; count += 1) row[count] = choose[length - 1][count - 1] + choose[length - 1][count];
    choose.push(row);
  }
  const answer = [];
  while (vertical > 0 && horizontal > 0) {
    const horizontalFirst = choose[vertical + horizontal - 1][horizontal - 1];
    if (k <= horizontalFirst) {
      answer.push('H');
      horizontal -= 1;
    } else {
      answer.push('V');
      vertical -= 1;
      k -= horizontalFirst;
    }
  }
  return answer.join('') + 'H'.repeat(horizontal) + 'V'.repeat(vertical);
}

const kthSmallestPath = solve;
class Solution {
  kthSmallestPath(destination, k) { return solve(destination, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, kthSmallestPath };
