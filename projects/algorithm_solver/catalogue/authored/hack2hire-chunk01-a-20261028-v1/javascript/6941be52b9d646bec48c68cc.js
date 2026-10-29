"use strict";
// Hack2Hire 6941be52b9d646bec48c68cc (Design Tennis Game, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
const CALLS = ["Love", "15", "30", "40"];
class TennisGame {
  constructor() { this.points = [0, 0]; this.winner = ""; }
  pointTo(player) {
    if (this.winner) return;
    const me = player === "A" ? 0 : 1;
    this.points[me] += 1;
    if (this.points[me] >= 4 && this.points[me] - this.points[1 - me] >= 2) this.winner = player;
  }
  getPoints() { return this.points.slice(); }
  getScore() {
    const [a, b] = this.points;
    if (this.winner) return "Game " + this.winner;
    if (a >= 3 && b >= 3) return a === b ? "Deuce" : "Advantage " + (a > b ? "A" : "B");
    return CALLS[a] + "-" + CALLS[b];
  }
  getWinner() { return this.winner; }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "TennisGame" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new TennisGame(...argumentLists[0]), allowed = new Set(["pointTo", "getPoints", "getScore", "getWinner"]), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.TennisGame = TennisGame;
