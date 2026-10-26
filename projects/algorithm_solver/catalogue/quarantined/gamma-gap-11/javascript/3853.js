'use strict';

// 3853. Merge Close Characters.
// O(n^2 k) time and O(n) space for n<=100; preserve the mandated leftmost-pair merge order.
function solve(s, k) {
  const characters = Array.from(s);
  while (true) {
    let removed = false;
    for (let left = 0; left < characters.length && !removed; left += 1) {
      for (let right = left + 1; right < Math.min(characters.length, left + k + 1); right += 1) {
        if (characters[left] === characters[right]) {
          characters.splice(right, 1);
          removed = true;
          break;
        }
      }
    }
    if (!removed) return characters.join('');
  }
}

const mergeCharacters = solve;
class Solution {
  mergeCharacters(s, k) { return solve(s, k); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, mergeCharacters };
