'use strict';

// 3821. Find Nth Smallest Integer With K One Bits.
// O(B^2) time and space, B=50; exact combinatorial unranking without 32-bit truncation.
function solve(n, k) {
  const choose = Array.from({ length: 51 }, () => Array(51).fill(0));
  for (let row = 0; row <= 50; row += 1) {
    choose[row][0] = 1;
    for (let column = 1; column <= row; column += 1) {
      choose[row][column] = choose[row - 1][column - 1] + choose[row - 1][column];
    }
  }
  let answer = 0;
  let needed = k;
  let rank = n;
  for (let bit = 49; bit >= 0; bit -= 1) {
    const without = needed <= bit ? choose[bit][needed] : 0;
    if (rank > without) {
      rank -= without;
      answer += 2 ** bit;
      needed -= 1;
    }
  }
  return answer;
}

const nthSmallest = solve;
class Solution {
  nthSmallest(n, k) { return solve(n, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, nthSmallest };
