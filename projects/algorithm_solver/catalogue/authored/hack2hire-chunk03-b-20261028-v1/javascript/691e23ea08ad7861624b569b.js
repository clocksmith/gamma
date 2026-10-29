"use strict";
// Hack2Hire 691e23ea08ad7861624b569b (Music Player, level 1) over an INFERRED spec; qualification unknown.

class MusicPlayer {
  constructor() {
    this.titles = [null];
    this.listeners = [null];
  }

  addSong(title) {
    this.titles.push(title);
    this.listeners.push(new Set());
    return this.titles.length - 1;
  }

  playSong(songId, userId) {
    this.listeners[songId].add(userId);
    return undefined;
  }

  getAnalytics() {
    const live = [];
    for (let i = 1; i < this.titles.length; i++) live.push(i);
    live.sort((a, b) => (this.listeners[b].size - this.listeners[a].size) || (a - b));
    return live.map((i) => [this.titles[i], this.listeners[i].size]);
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "MusicPlayer" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new MusicPlayer();
  const allowed = new Set(["addSong", "playSong", "getAnalytics"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.MusicPlayer = MusicPlayer;
