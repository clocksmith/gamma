"use strict";
// Hack2Hire 6986db08fedd959e9aa443ca (Design Card Game II, variant 2) over an INFERRED spec; qualification unknown.
const SUITS = ["CLUBS", "DIAMONDS", "HEARTS", "SPADES"];
const RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"];
function solve(shuffledDeck, players) {
  const dealt = Math.floor(52 / players) * players;
  const held = Array.from({length: players}, () => new Uint8Array(52));
  for (let i = 0; i < dealt; i++) {
    const [suit, rank] = shuffledDeck[i];
    held[i % players][SUITS.indexOf(suit) * 13 + RANKS.indexOf(rank)] = 1;
  }
  return held.map((marks) => {
    const hand = [];
    for (let k = 0; k < 52; k++) if (marks[k]) hand.push([SUITS[Math.floor(k / 13)], RANKS[k % 13]]);
    return hand;
  });
}
function dealAndSortHands(shuffledDeck, players) { return solve(shuffledDeck, players); }
module.exports = solve;
module.exports.dealAndSortHands = dealAndSortHands;
