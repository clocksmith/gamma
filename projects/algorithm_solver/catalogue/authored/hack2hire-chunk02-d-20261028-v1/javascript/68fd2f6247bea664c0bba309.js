"use strict";
// Hack2Hire 68fd2f6247bea664c0bba309 (Friend Recommendations by Mutual Friends) over an INFERRED spec; qualification unknown.

function solve(n, friendships) {
  const adjacency = Array.from({length: n}, () => []);
  for (const [a, b] of friendships) { adjacency[a].push(b); adjacency[b].push(a); }
  const count = new Int32Array(n);
  const blocked = new Int32Array(n).fill(-1);
  const result = [];
  for (let user = 0; user < n; user++) {
    blocked[user] = user;
    for (const friend of adjacency[user]) blocked[friend] = user;
    const touched = [];
    for (const friend of adjacency[user]) {
      for (const other of adjacency[friend]) {
        if (blocked[other] === user) continue;
        if (count[other] === 0) touched.push(other);
        count[other]++;
      }
    }
    let best = 0, pick = -1;
    for (const other of touched) {
      if (count[other] > best || (count[other] === best && other < pick)) { best = count[other]; pick = other; }
      count[other] = 0;
    }
    result.push(pick);
  }
  return result;
}

function recommendFriends(n, friendships) { return solve(n, friendships); }

module.exports = solve;
module.exports.recommendFriends = recommendFriends;
