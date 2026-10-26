'use strict';

// 1583. Count Unhappy Friends: use preference ranks to detect mutually preferable alternative partners.
// O(n^2) time and O(n^2) auxiliary space; inputs are read-only.
function solve(n, preferences, pairs) {
  const rank = Array.from({ length: n }, () => new Int32Array(n));
  for (let person = 0; person < n; person += 1) {
    for (let position = 0; position < preferences[person].length; position += 1) {
      rank[person][preferences[person][position]] = position;
    }
  }
  const partner = new Int32Array(n).fill(-1);
  for (const [first, second] of pairs) {
    partner[first] = second;
    partner[second] = first;
  }
  let unhappy = 0;
  for (let person = 0; person < n; person += 1) {
    for (const other of preferences[person]) {
      if (other === partner[person]) break;
      if (rank[other][person] < rank[other][partner[other]]) {
        unhappy += 1;
        break;
      }
    }
  }
  return unhappy;
}

const unhappyFriends = solve;
class Solution {
  unhappyFriends(n, preferences, pairs) { return solve(n, preferences, pairs); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, unhappyFriends };
