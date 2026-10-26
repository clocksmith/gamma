'use strict';

// 2734. Lexicographically Smallest String After Substring Operation: decrease the first non-a run or wrap the final a when every character is a.
// O(n) time and O(n) auxiliary space; inputs are read-only.
function solve(s) {
  const characters = s.split('');
  let index = 0;
  while (index < characters.length && characters[index] === 'a') index += 1;
  if (index === characters.length) characters[characters.length - 1] = 'z';
  else {
    while (index < characters.length && characters[index] !== 'a') {
      characters[index] = String.fromCharCode(characters[index].charCodeAt(0) - 1);
      index += 1;
    }
  }
  return characters.join('');
}

const smallestString = solve;
class Solution {
  smallestString(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, smallestString };
