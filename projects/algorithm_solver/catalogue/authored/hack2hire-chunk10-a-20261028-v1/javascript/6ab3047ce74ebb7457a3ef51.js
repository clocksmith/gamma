"use strict";
// Hack2Hire 6ab3047ce74ebb7457a3ef51 (Design Card Game III, variant 3 of 3) over an INFERRED spec; qualification unknown.

const RANK = new Map(["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"].map((r, i) => [r, i]));

function handKey(hand) {
  // flat strength key: category, then tie-break ranks in significance order
  const ranks = hand.map((c) => RANK.get(c.slice(0, -1))).sort((a, b) => b - a);
  const distinct = new Set(ranks).size;
  if (distinct === 1) return [3, ranks[0]];
  if (distinct === 2) {
    const pair = ranks[1]; // the middle of three sorted ranks always belongs to the pair
    return [2, pair, ranks[0] !== pair ? ranks[0] : ranks[2]];
  }
  return [1, ...ranks];
}

function compareKeys(a, b) {
  for (let i = 0; i < Math.min(a.length, b.length); i++) if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1;
  return a.length - b.length;
}

function solve(numPlayers, deck) {
  const hands = [];
  for (let p = 0; p < numPlayers; p++) hands.push([deck[p], deck[p + numPlayers], deck[p + 2 * numPlayers]]);
  let best = null, winners = [];
  hands.forEach((hand, p) => {
    const key = handKey(hand);
    const c = best === null ? 1 : compareKeys(key, best);
    if (c > 0) { best = key; winners = [p + 1]; } else if (c === 0) winners.push(p + 1);
  });
  return [hands, winners];
}

function playTable(numPlayers, deck) { return solve(numPlayers, deck); }

module.exports = solve;
module.exports.playTable = playTable;
