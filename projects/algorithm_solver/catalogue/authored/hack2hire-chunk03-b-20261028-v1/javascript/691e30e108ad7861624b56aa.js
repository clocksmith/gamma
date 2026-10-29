"use strict";
// Hack2Hire 691e30e108ad7861624b56aa (Music Player, level 2) over an INFERRED spec; qualification unknown.

class MusicPlayer {
  constructor() {
    this.titles = [null];
    this.listeners = [null];
    this.recent = new Map();
  }

  addSong(title) {
    this.titles.push(title);
    this.listeners.push(new Set());
    return this.titles.length - 1;
  }

  playSong(songId, userId) {
    this.listeners[songId].add(userId);
    let user = this.recent.get(userId);
    if (user === undefined) { user = {head: 0, next: new Map(), prev: new Map()}; this.recent.set(userId, user); }
    if (user.next.has(songId)) this._unlink(user, songId);
    const head = user.head;
    user.next.set(songId, head); user.prev.set(songId, 0);
    if (head) user.prev.set(head, songId);
    user.head = songId;
    return undefined;
  }

  getAnalytics() {
    const live = [];
    for (let i = 1; i < this.titles.length; i++) live.push(i);
    live.sort((a, b) => (this.listeners[b].size - this.listeners[a].size) || (a - b));
    return live.map((i) => [this.titles[i], this.listeners[i].size]);
  }

  _unlink(user, song) {
    const before = user.prev.get(song), after = user.next.get(song);
    user.prev.delete(song); user.next.delete(song);
    if (before) user.next.set(before, after); else user.head = after;
    if (after) user.prev.set(after, before);
  }

  getLastThreeSongs(userId) {
    const user = this.recent.get(userId), result = [];
    if (user === undefined) return result;
    let song = user.head;
    while (song && result.length < 3) {
      const after = user.next.get(song);
      result.push(song);
      song = after;
    }
    return result;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "MusicPlayer" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new MusicPlayer();
  const allowed = new Set(["addSong", "playSong", "getAnalytics", "getLastThreeSongs"]);
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
