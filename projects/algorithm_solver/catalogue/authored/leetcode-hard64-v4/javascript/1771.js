'use strict';

// 1771. Maximize Palindrome Length From Subsequences. Interval DP with a crossing endpoint pair; O(L^2) time and O(L) space. Inputs are preserved.

function solve(word1, word2) {
  const text = word1 + word2;
  const size = text.length;
  const boundary = word1.length;
  const best = Array(size).fill(0);
  let answer = 0;
  for (let left = size - 1; left >= 0; left -= 1) {
    let diagonal = 0;
    best[left] = 1;
    for (let right = left + 1; right < size; right += 1) {
      const previous = best[right];
      if (text[left] === text[right]) {
        best[right] = diagonal + 2;
        if (left < boundary && right >= boundary) answer = Math.max(answer, best[right]);
      } else {
        best[right] = Math.max(best[right], best[right - 1]);
      }
      diagonal = previous;
    }
  }
  return answer;
}

const longestPalindrome = solve;
class Solution {
  longestPalindrome(word1, word2) { return solve(word1, word2); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, longestPalindrome };
