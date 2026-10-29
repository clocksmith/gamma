"use strict";
// Hack2Hire 681bc967a73bd75b806cb994 (Escape Room) over an INFERRED spec; qualification unknown.

class EscapeRoom {
  constructor(n, m) {
    this.n = n;
    this.room = new Array(m).fill(0);
    this.prev = Array.from({length: m}, (_, p) => p - 1);
    this.next = Array.from({length: m}, (_, p) => (p + 1 < m ? p + 1 : -1));
    this.head = new Array(n).fill(-1);
    this.tail = new Array(n).fill(-1);
    this.count = new Array(n).fill(0);
    this.head[0] = 0;
    this.tail[0] = m - 1;
    this.count[0] = m;
    // non-empty rooms in decreasing order, as a linked list
    this.lower = new Array(n).fill(-1);
    this.higher = new Array(n).fill(-1);
    this.top = 0;
  }

  advance(player) {
    const r = this.room[player];
    if (r === this.n - 1) return;
    const p = this.prev[player], q = this.next[player];
    if (p >= 0) this.next[p] = q;
    else this.head[r] = q;
    if (q >= 0) this.prev[q] = p;
    else this.tail[r] = p;
    const s = r + 1;
    if (this.count[s] === 0) {
      const above = this.higher[r];
      this.higher[s] = above;
      this.lower[s] = r;
      this.higher[r] = s;
      if (above >= 0) this.lower[above] = s;
      else this.top = s;
    }
    const t = this.tail[s];
    this.prev[player] = t;
    this.next[player] = -1;
    if (t >= 0) this.next[t] = player;
    else this.head[s] = player;
    this.tail[s] = player;
    this.count[s]++;
    this.room[player] = s;
    this.count[r]--;
    if (this.count[r] === 0) {
      const below = this.lower[r], above = this.higher[r];
      if (below >= 0) this.higher[below] = above;
      if (above >= 0) this.lower[above] = below;
      else this.top = below;
    }
  }

  countInRoom(room) {
    return this.count[room];
  }

  topPlayers(k) {
    const result = [];
    let r = this.top;
    while (r >= 0 && result.length < k) {
      let p = this.head[r];
      while (p >= 0 && result.length < k) {
        result.push(p);
        p = this.next[p];
      }
      r = this.lower[r];
    }
    return result;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "EscapeRoom" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new EscapeRoom(...argumentLists[0]);
  const allowed = new Set(["advance", "countInRoom", "topPlayers"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.EscapeRoom = EscapeRoom;
