'use strict';

// 2663. Lexicographically Smallest Beautiful String.
// O(n*k) time, O(n) space. A palindrome of length >=2 contains a length-2 or length-3 palindrome.
function solve(s, k) {
  const letters = Array.from(s, char => char.charCodeAt(0) - 97);
  for (let index = letters.length - 1; index >= 0; index -= 1) {
    for (let candidate = letters[index] + 1; candidate < k; candidate += 1) {
      if (index >= 1 && candidate === letters[index - 1]) continue;
      if (index >= 2 && candidate === letters[index - 2]) continue;
      letters[index] = candidate;
      for (let following = index + 1; following < letters.length; following += 1) {
        let smallest = 0;
        while (smallest === letters[following - 1]
          || (following >= 2 && smallest === letters[following - 2])) smallest += 1;
        letters[following] = smallest;
      }
      return letters.map(letter => String.fromCharCode(97 + letter)).join('');
    }
  }
  return '';
}

const smallestBeautifulString = solve;
class Solution {
  smallestBeautifulString(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestBeautifulString };
