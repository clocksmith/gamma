"use strict";
// Hack2Hire 68fd5b9d47bea664c0bba367 (Poker Straight Sequence Check) over an INFERRED spec; qualification unknown.

const RANK = {A: 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9, "10": 10, J: 11, Q: 12, K: 13};

function solve(cards) {
  const low = cards.map((c) => RANK[c]);
  if (Math.max(...low) - Math.min(...low) === 4) return true; // five distinct values spanning 4 are consecutive
  const high = low.map((r) => (r === 1 ? 14 : r));
  return Math.max(...high) - Math.min(...high) === 4;
}

function isStraight(cards) { return solve(cards); }

module.exports = solve;
module.exports.isStraight = isStraight;
