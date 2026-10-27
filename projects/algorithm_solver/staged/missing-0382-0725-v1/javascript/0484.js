'use strict';

// 484. Find Permutation. Reverse exactly the maximal descending runs in the initial increasing permutation.

function solve(s) {
  const answer = Array.from({length: s.length + 1}, (_, i) => i + 1);
  let i = 0;
  while (i < s.length) {
    if (s[i] === 'I') { i += 1; continue; }
    let j = i;
    while (j < s.length && s[j] === 'D') j += 1;
    for (let a = i, b = j; a < b; a += 1, b -= 1) [answer[a], answer[b]] = [answer[b], answer[a]];
    i = j;
  }
  return answer;
}

const findPermutation = solve;
class Solution {
  findPermutation(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, findPermutation };
