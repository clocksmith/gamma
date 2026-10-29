"use strict";
// Hack2Hire 68672293a2d59460201f2cae (Delete k Elements to Balance) over an INFERRED spec; qualification unknown.

function solve(nums, k) {
  const n = nums.length, even = new Array(n + 1).fill(0), odd = new Array(n + 1).fill(0);
  for (let i = 0; i < n; i++) {
    even[i + 1] = even[i] + (i % 2 === 0 ? nums[i] : 0);
    odd[i + 1] = odd[i] + (i % 2 ? nums[i] : 0);
  }
  for (let i = 0; i + k <= n; i++) {
    let tailEven = even[n] - even[i + k], tailOdd = odd[n] - odd[i + k];
    if (k % 2) [tailEven, tailOdd] = [tailOdd, tailEven];
    if (even[i] + tailEven === odd[i] + tailOdd) return i;
  }
  return -1;
}

function balanceStart(nums, k) { return solve(nums, k); }

module.exports = solve;
module.exports.balanceStart = balanceStart;
