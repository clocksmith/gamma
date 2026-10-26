'use strict';

// 1415. The k-th Lexicographical String of All Happy Strings of Length n: skip lexicographic blocks using their exact binary suffix counts.
// O(n) time and O(n) space including the result on the declared n <= 10 domain; inputs are read-only.
function solve(n, k) {
  if (k > 3 * 2 ** (n - 1)) return '';
  const result = [];
  let rank = k;
  for (let index = 0; index < n; index += 1) {
    const block = 2 ** (n - index - 1);
    for (const letter of 'abc') {
      if (result.length && result[result.length - 1] === letter) continue;
      if (rank > block) rank -= block;
      else {
        result.push(letter);
        break;
      }
    }
  }
  return result.join('');
}

const getHappyString = solve;
class Solution {
  getHappyString(n, k) { return solve(n, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, getHappyString };
