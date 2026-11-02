"use strict";

function solve(s, t) {
  if (s.length > t.length) {
    const tmp = s; s = t; t = tmp;
  }
  if (t.length - s.length > 1) return false;
  for (let i = 0; i < s.length; i++) {
    if (s.charCodeAt(i) !== t.charCodeAt(i)) {
      if (s.length === t.length) return s.slice(i + 1) === t.slice(i + 1);
      return s.slice(i) === t.slice(i + 1);
    }
  }
  return t.length === s.length + 1;
}

function isOneEditDistance(s, t) {
  return solve(s, t);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.isOneEditDistance = isOneEditDistance;
