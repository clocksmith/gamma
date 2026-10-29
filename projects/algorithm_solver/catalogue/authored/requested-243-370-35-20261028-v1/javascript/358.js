"use strict";

function solve(s, k) {
  if (k <= 1) return s;
  const cnt = new Map();
  for (let i = 0; i < s.length; i++) {
    const ch = s[i];
    cnt.set(ch, (cnt.get(ch) || 0) + 1);
  }
  const avail = [];
  for (const [ch, c] of cnt.entries()) {
    avail.push([-c, ch.charCodeAt(0), ch]);
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
  return res.length === s.length ? res.join("") : "";
}

function rearrangeString(s, k) {
  return solve(s, k);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.rearrangeString = rearrangeString;
