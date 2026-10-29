"use strict";
// Hack2Hire 67fa9534ba41b3368f4e5851 (Random User Pairing, variant 1 of 2) over an INFERRED spec; qualification unknown.

function solve(users, randomInts) {
  const pool = users.slice(), pairs = [];
  let size = pool.length, k = 0;
  while (size >= 2) {
    const i = randomInts[k] % size, first = pool[i];
    size--; pool[i] = pool[size];
    const j = randomInts[k + 1] % size, second = pool[j];
    size--; pool[j] = pool[size];
    k += 2;
    pairs.push([first, second]);
  }
  if (size === 1) pairs.push([pool[0]]);
  return pairs;
}

function pairUsers(users, randomInts) { return solve(users, randomInts); }

module.exports = solve;
module.exports.pairUsers = pairUsers;
