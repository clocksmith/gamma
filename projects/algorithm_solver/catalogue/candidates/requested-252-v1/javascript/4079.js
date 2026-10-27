'use strict';

// 4079. Prime Subset Selection I.
// Specification: https://leetcode.com/problems/prime-subset-selection-i/description/
// O(n log log n) time and O(n) space; the smallest-prime prefix maximizes cardinality. Inputs are preserved.
function solve(n, s) {
  const composite = new Uint8Array(n + 1);
  for (let prime = 2; prime * prime <= n; prime++) {
    if (!composite[prime]) for (let multiple = prime * prime; multiple <= n; multiple += prime) composite[multiple] = 1;
  }
  const answer = [];
  let total = 0;
  for (let prime = 2; prime <= n; prime++) {
    if (composite[prime]) continue;
    if (total + prime > s) break;
    answer.push(prime);
    total += prime;
  }
  return answer;
}

if (typeof module !== 'undefined') module.exports = { solve };
