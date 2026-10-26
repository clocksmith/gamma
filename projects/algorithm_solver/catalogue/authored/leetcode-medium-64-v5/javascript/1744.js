'use strict';

// 1744. Can You Eat Your Favorite Candy on Your Favorite Day?: intersect the possible consumption range with each candy-type interval.
// O(n + q) time and O(n + q) space, with n candy types and q queries; inputs are read-only.
function solve(candiesCount, queries) {
  const prefix = [0];
  for (const count of candiesCount) prefix.push(prefix[prefix.length - 1] + count);
  const result = [];
  for (const [kind, day, cap] of queries) {
    // Prefix sums are exact Numbers; avoid the unsafe day * cap product.
    result.push(day < prefix[kind + 1] && Math.floor(prefix[kind] / cap) <= day);
  }
  return result;
}

const canEat = solve;
class Solution {
  canEat(candiesCount, queries) { return solve(candiesCount, queries); }
}
if (typeof module !== 'undefined') module.exports = { solve, Solution, canEat };
