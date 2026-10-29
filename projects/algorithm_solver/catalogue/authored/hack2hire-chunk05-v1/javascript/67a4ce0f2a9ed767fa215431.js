// Original hack2hire:67a4ce0f2a9ed767fa215431; inferred public-preview contract; qualification unknown.
"use strict";
function countDistinctPasswords(password) {
  let seen = 0, result = 1;
  const counts = new Map();
  for (const ch of password) {
    result += seen - (counts.get(ch) || 0);
    counts.set(ch, (counts.get(ch) || 0) + 1);
    seen++;
  }
  return result;
}

const solve = countDistinctPasswords;
module.exports = solve;
module.exports.countDistinctPasswords = countDistinctPasswords;
module.exports.Solution = class { countDistinctPasswords(...args) { return countDistinctPasswords(...args); } };
