"use strict";
// Hack2Hire 67842117d0faf7ec64cc3add (Design Card Game, variant 1) over an INFERRED spec; qualification unknown.

class CardGame {
  constructor(deck) {
    this.deck = deck.slice();
    this.position = 0;
    this.scores = {A: 0, B: 0};
  }

  playRound() {
    if (this.position + 2 > this.deck.length) return "";
    const a = this.deck[this.position], b = this.deck[this.position + 1];
    this.position += 2;
    const winner = a > b ? "A" : "B";
    this.scores[winner] += 1;
    return winner;
  }

  getScore(player) {
    return this.scores[player];
  }

  getWinner() {
    if (this.position < this.deck.length) return "";
    const a = this.scores.A, b = this.scores.B;
    return a === b ? "TIE" : (a > b ? "A" : "B");
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "CardGame" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new CardGame(...argumentLists[0]);
  const allowed = new Set(["playRound", "getScore", "getWinner"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    result.push(instance[operationNames[i]](...argumentLists[i]));
  }
  return result;
}

module.exports = solve;
module.exports.CardGame = CardGame;
