"use strict";

const MOD = 1000000007;

function solve(nums, queries) {
  const n = nums.length;
  const B = Math.floor(Math.sqrt(n)) + 1;
  const suf = new Array(B);
  for (let y = 1; y < B; y++) {
    const arr = new Int32Array(n);
    for (let i = n - 1; i >= 0; i--) {
      arr[i] = (nums[i] + (i + y < n ? arr[i + y] : 0)) % MOD;
    }
    suf[y] = arr;
  }
  const out = new Array(queries.length);
  for (let q = 0; q < queries.length; q++) {
    const [x, y] = queries[q];
    if (y < B) {
      out[q] = suf[y][x];
    } else {
      let s = 0;
      for (let i = x; i < n; i += y) s = (s + nums[i]) % MOD;
      out[q] = s;
    }
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
