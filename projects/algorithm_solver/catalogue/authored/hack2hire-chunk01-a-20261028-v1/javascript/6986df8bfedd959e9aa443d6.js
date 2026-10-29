"use strict";
// Hack2Hire 6986df8bfedd959e9aa443d6 (Design Card Game II, variant 3) over an INFERRED spec; qualification unknown.
const SUITS = ["CLUBS", "DIAMONDS", "HEARTS", "SPADES"];
const RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"];
function solve(shuffledDeck, players) {
  const size = Math.floor(52 / players), hands = Array.from({length: players}, () => []);
  for (let i = 0; i < size * players; i++) {
    const [suit, rank] = shuffledDeck[i];
    hands[i % players].push(RANKS.indexOf(rank) * 4 + SUITS.indexOf(suit)); // strength: rank first, suit breaks ties
  }
  for (const hand of hands) hand.sort((a, b) => b - a);
  const wins = new Array(players).fill(0);
  for (let round = 0; round < size; round++) {
    let best = 0;
    for (let p = 1; p < players; p++) if (hands[p][round] > hands[best][round]) best = p;
    wins[best] += 1;
  }
  return wins;
}
function playRounds(shuffledDeck, players) { return solve(shuffledDeck, players); }
module.exports = solve;
module.exports.playRounds = playRounds;
