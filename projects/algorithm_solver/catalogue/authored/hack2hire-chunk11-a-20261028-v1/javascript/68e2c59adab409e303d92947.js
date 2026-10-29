"use strict";
// Hack2Hire 68e2c59adab409e303d92947 (Friends by Last-K Movie Overlap, variant 1 of 2) over an INFERRED spec; qualification unknown.

function solve(customerIds, movies, k) {
  const groups = new Map(); // insertion order follows each group's first member
  customerIds.forEach((customer, i) => {
    const history = movies[i];
    if (history.length < k) return;
    const key = [...new Set(history.slice(history.length - k))].sort().join(",");
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(customer);
  });
  return [...groups.values()].filter((group) => group.length >= 2);
}

function findFriendGroups(customerIds, movies, k) { return solve(customerIds, movies, k); }

module.exports = solve;
module.exports.findFriendGroups = findFriendGroups;
