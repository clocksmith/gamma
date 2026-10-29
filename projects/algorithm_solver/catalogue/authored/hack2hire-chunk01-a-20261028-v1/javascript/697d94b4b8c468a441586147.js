"use strict";
// Hack2Hire 697d94b4b8c468a441586147 (Design Card Game II, variant 1) over an INFERRED spec; qualification unknown.
const SUITS = ["CLUBS", "DIAMONDS", "HEARTS", "SPADES"];
const RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"];
function solve(shuffledDeck) {
  const players = 4, dealt = 52;
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
function dealAndSortHands(shuffledDeck) { return solve(shuffledDeck); }
module.exports = solve;
module.exports.dealAndSortHands = dealAndSortHands;
