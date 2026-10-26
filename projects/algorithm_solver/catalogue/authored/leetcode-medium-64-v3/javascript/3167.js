'use strict';

// 3167. Better Compression of String: parse full decimal counts and combine them in alphabetic order.
// O(n) time and O(26) auxiliary space excluding output; inputs are read-only.
function solve(compressed) {
  const counts = new Array(26).fill(0);
  let index = 0;
  while (index < compressed.length) {
    const letter = compressed.charCodeAt(index) - 97;
    index += 1;
    let count = 0;
    while (index < compressed.length && compressed[index] >= '0' && compressed[index] <= '9') {
      count = count * 10 + compressed.charCodeAt(index) - 48;
      index += 1;
    }
    counts[letter] += count;
  }
  const result = [];
  for (let letter = 0; letter < 26; letter += 1) {
    if (counts[letter] !== 0) result.push(String.fromCharCode(97 + letter) + String(counts[letter]));
  }
  return result.join('');
}

const betterCompression = solve;
class Solution {
  betterCompression(compressed) { return solve(compressed); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, betterCompression };
