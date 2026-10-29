"use strict";

function solve(strings) {
  const groups = new Map();
  for (let i = 0; i < strings.length; i++) {
    const s = strings[i];
    const base = s.charCodeAt(0);
    const parts = new Array(s.length);
    for (let j = 0; j < s.length; j++) {
      parts[j] = (s.charCodeAt(j) - base + 26) % 26;
    }
    const key = parts.join(",");
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(s);
  }
  return Array.from(groups.values());
}

function groupStrings(strings) {
  return solve(strings);
}

module.exports = solve;
module.exports.solve = solve;
module.exports.groupStrings = groupStrings;
