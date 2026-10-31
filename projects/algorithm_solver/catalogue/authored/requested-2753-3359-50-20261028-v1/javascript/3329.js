"use strict";

function solve(s, k) {
  const cnt = new Int32Array(26);
  let left = 0;
  let ans = 0;
  const n = s.length;
  for (let right = 0; right < n; right++) {
    const c = s.charCodeAt(right) - 97;
    cnt[c]++;
    while (cnt[c] >= k) {
      ans += n - right;
      cnt[s.charCodeAt(left) - 97]--;
      left++;
    }
  }
  return ans;
}

function numberOfSubstrings(s, k) {
  return solve(s, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.numberOfSubstrings = numberOfSubstrings;
