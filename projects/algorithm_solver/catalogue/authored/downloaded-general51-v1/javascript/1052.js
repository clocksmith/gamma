'use strict';

// 1052. Grumpy Bookstore Owner (Medium).
// Specification: https://leetcode.com/problems/grumpy-bookstore-owner/description/
function solve(customers, grumpy, minutes) {
  let base = 0;
  for (let i = 0; i < customers.length; i++) { if (grumpy[i] === 0) base += customers[i]; }
  let extra = 0; let window = 0;
  for (let i = 0; i < customers.length; i++) {
    if (grumpy[i] === 1) window += customers[i];
    if (i >= minutes && grumpy[i - minutes] === 1) window -= customers[i - minutes];
    extra = Math.max(extra, window);
  }
  return base + extra;
}
const maxSatisfied = solve;
class Solution { maxSatisfied(customers, grumpy, minutes) { return solve(customers, grumpy, minutes); } }
if (typeof module !== 'undefined') module.exports = { solve, Solution, maxSatisfied };
