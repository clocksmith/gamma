"use strict";
// Hack2Hire 6941c912e79fe20cf9ff4435 (Design Tennis Game, variant 2) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
const CALLS = ["Love", "15", "30", "40"];
class TennisSet {
  constructor() { this.games = [0, 0]; this.points = [0, 0]; this.tiebreak = false; this.winner = ""; }
  pointTo(player) {
    if (this.winner) return;
    const me = player === "A" ? 0 : 1;
    this.points[me] += 1;
    const need = this.tiebreak ? 7 : 4;
    if (this.points[me] < need || this.points[me] - this.points[1 - me] < 2) return;
    this.points = [0, 0];
    this.games[me] += 1;
    if (this.tiebreak || (this.games[me] >= 6 && this.games[me] - this.games[1 - me] >= 2)) { this.winner = player; this.tiebreak = false; }
    else if (this.games[0] === 6 && this.games[1] === 6) this.tiebreak = true;
  }
  getGames() { return this.games.slice(); }
  getGameScore() {
    if (this.winner) return "Set " + this.winner;
    const [a, b] = this.points;
    if (this.tiebreak) return "Tiebreak " + a + "-" + b;
    if (a >= 3 && b >= 3) return a === b ? "Deuce" : "Advantage " + (a > b ? "A" : "B");
    return CALLS[a] + "-" + CALLS[b];
  }
  getWinner() { return this.winner; }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "TennisSet" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new TennisSet(...argumentLists[0]), allowed = new Set(["pointTo", "getGames", "getGameScore", "getWinner"]), result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.TennisSet = TennisSet;
