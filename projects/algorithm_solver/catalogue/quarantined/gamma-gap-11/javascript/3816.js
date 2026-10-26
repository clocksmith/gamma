'use strict';

// 3816. Lexicographically Smallest String After Deleting Duplicate Characters.
// O(n) time and space; keep useful duplicates, remove only dispensable inversions and suffix characters.
function solve(s) {
  const remaining = Array(26).fill(0);
  for (const char of s) remaining[char.charCodeAt(0) - 97] += 1;
  const stack = [];
  for (const char of s) {
    while (stack.length > 0 && stack[stack.length - 1] > char && remaining[stack[stack.length - 1].charCodeAt(0) - 97] > 1) {
      remaining[stack.pop().charCodeAt(0) - 97] -= 1;
    }
    stack.push(char);
  }
  while (stack.length > 0 && remaining[stack[stack.length - 1].charCodeAt(0) - 97] > 1) {
    remaining[stack.pop().charCodeAt(0) - 97] -= 1;
  }
  return stack.join('');
}

const lexSmallestAfterDeletion = solve;
class Solution {
  lexSmallestAfterDeletion(s) { return solve(s); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, lexSmallestAfterDeletion };
