"use strict";

class Leaderboard {
  constructor() {
    this.scores = new Map();
  }
  addScore(playerId, score) {
    this.scores.set(playerId, (this.scores.get(playerId) || 0) + score);
  }
  top(K) {
    const vals = Array.from(this.scores.values()).sort((a, b) => b - a);
    let s = 0;
    for (let i = 0; i < K && i < vals.length; i++) s += vals[i];
    return s;
  }
  reset(playerId) {
    this.scores.delete(playerId);
  }
}

function solve(operation_names, argument_lists) {
  const inst = new Leaderboard();
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i], args = argument_lists[i];
    if (op === "addScore") { inst.addScore(args[0], args[1]); out.push(null); }
    else if (op === "top") out.push(inst.top(args[0]));
    else { inst.reset(args[0]); out.push(null); }
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.Leaderboard = Leaderboard;
