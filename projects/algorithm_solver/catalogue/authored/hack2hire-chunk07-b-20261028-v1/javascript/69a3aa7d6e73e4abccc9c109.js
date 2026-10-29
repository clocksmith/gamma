"use strict";
// Hack2Hire 69a3aa7d6e73e4abccc9c109 (Monster Team Battle, level 1) over an INFERRED spec; qualification unknown.

const LEVEL = 1;

function solve(teamA, teamB) {
  const teams = [teamA, teamB];
  const health = [teamA.map((m) => m.health), teamB.map((m) => m.health)];
  const front = [0, 0];
  const log = [];
  const attack = (side) => {
    const other = 1 - side;
    const attacker = teams[side][front[side]], defender = teams[other][front[other]];
    const damage = LEVEL === 1 ? attacker.attack : Math.max(1, attacker.attack - defender.defense);
    const left = health[other][front[other]] - damage;
    health[other][front[other]] = left;
    log.push(attacker.name + " attacks " + defender.name + " for " + damage + " damage, " + defender.name + " has " + Math.max(0, left) + " health left");
    if (left <= 0) { log.push(defender.name + " is defeated"); front[other]++; return true; }
    return false;
  };
  let turn = 0;
  while (front[0] < teamA.length && front[1] < teamB.length) {
    if (LEVEL === 3) {
      const first = teamA[front[0]].speed >= teamB[front[1]].speed ? 0 : 1;
      if (!attack(first)) attack(1 - first);
    } else { attack(turn); turn = 1 - turn; }
  }
  log.push(front[0] < teamA.length ? "Team A wins" : "Team B wins");
  return log;
}

function battleLog(teamA, teamB) { return solve(teamA, teamB); }

module.exports = solve;
module.exports.battleLog = battleLog;
