"use strict";
// Hack2Hire 679da470996c3c60bd38b5ba (Alien Base Attack) over an INFERRED spec; qualification unknown.

class AlienBaseAttack {
  constructor(n) {
    this.n = n;
    this.destroyed = new Set();
  }

  attack(x) {
    if (x >= 0 && x < this.n) this.destroyed.add(x);
  }

  isDestroyed() {
    return this.destroyed.size === this.n;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "AlienBaseAttack" || argumentLists[0].length !== 1) throw new Error("exact initial constructor required");
  const instance = new AlienBaseAttack(...argumentLists[0]);
  const allowed = new Set(["attack", "isDestroyed"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.AlienBaseAttack = AlienBaseAttack;
