"use strict";

// string_unit = unicode_codepoint: counts code points and breaks ties by code
// point (matching the reference's ord), so non-BMP characters are never split.
function solve(s, k) {
  if (k <= 1) return s;
  const cnt = new Map();
  let total = 0;
  for (const ch of s) {
    cnt.set(ch, (cnt.get(ch) || 0) + 1);
    total++;
  }
  const avail = [];
  for (const [ch, c] of cnt.entries()) {
    avail.push([-c, ch.codePointAt(0), ch]);
  }
  const q = [];
  let qHead = 0;
  const res = [];
  while (avail.length > 0) {
    avail.sort((a, b) => (a[0] !== b[0] ? a[0] - b[0] : a[1] - b[1]));
    const [negC, code, ch] = avail.shift();
    res.push(ch);
    q.push([negC + 1, code, ch]);
    if (q.length - qHead >= k) {
      const item = q[qHead++];
      if (item[0] < 0) avail.push(item);
    }
  }
  return res.length === total ? res.join("") : "";
}

function rearrangeString(s, k) {
  return solve(s, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.rearrangeString = rearrangeString;
if (typeof Solution !== "undefined") solve.Solution = Solution;
