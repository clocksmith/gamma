"use strict";
// Hack2Hire 6ab3042be74ebb7457a3ef4a (Design Card Game III, variant 2 of 3) over an INFERRED spec; qualification unknown.

const RANK = new Map(["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"].map((r, i) => [r, i]));

function handKey(hand) {
  // flat strength key: category, then tie-break ranks in significance order
  const ranks = hand.map((c) => RANK.get(c.slice(0, -1))).sort((a, b) => b - a);
  const distinct = new Set(ranks).size;
  if (distinct === 1) return [5, ranks[0]];
  if (distinct === 2) {
    const pair = ranks[1]; // the middle of three sorted ranks always belongs to the pair
    return [2, pair, ranks[0] !== pair ? ranks[0] : ranks[2]];
  }
  const straight = ranks[0] - 1 === ranks[1] && ranks[1] - 1 === ranks[2];
  const flush = hand[0].slice(-1) === hand[1].slice(-1) && hand[1].slice(-1) === hand[2].slice(-1);
  if (straight && flush) return [6, ...ranks];
  if (straight) return [4, ...ranks];
  if (flush) return [3, ...ranks];
  return [1, ...ranks];
}

function compareKeys(a, b) {
  for (let i = 0; i < Math.min(a.length, b.length); i++) if (a[i] !== b[i]) return a[i] < b[i] ? -1 : 1;
  return a.length - b.length;
}

function solve(deck) {
  const first = [deck[0], deck[2], deck[4]], second = [deck[1], deck[3], deck[5]];
  const c = compareKeys(handKey(first), handKey(second));
  return [first, second, c > 0 ? 1 : c < 0 ? 2 : 0];
}

function playRound(deck) { return solve(deck); }

module.exports = solve;
module.exports.playRound = playRound;
