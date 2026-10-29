"use strict";

class FileSharing {
  constructor(m) {
    this.m = m;
    this.freeIds = [];
    this.nextId = 1;
    this.userChunks = new Map();
    this.chunkUsers = new Map();
  }
  join(ownedChunks) {
    let uid;
    if (this.freeIds.length > 0) {
      this.freeIds.sort((a, b) => a - b);
      uid = this.freeIds.shift();
    } else {
      uid = this.nextId++;
    }
    const chunks = new Set(ownedChunks);
    this.userChunks.set(uid, chunks);
    for (const c of chunks) {
      let s = this.chunkUsers.get(c);
      if (!s) { s = new Set(); this.chunkUsers.set(c, s); }
      s.add(uid);
    }
    return uid;
  }
  leave(userID) {
    const chunks = this.userChunks.get(userID) || [];
    this.userChunks.delete(userID);
    for (const c of chunks) {
      const s = this.chunkUsers.get(c);
      if (s) s.delete(userID);
    }
    this.freeIds.push(userID);
  }
  request(userID, chunkID) {
    const s = this.chunkUsers.get(chunkID);
    const owners = s ? Array.from(s).sort((a, b) => a - b) : [];
    if (owners.length > 0) {
      this.userChunks.get(userID).add(chunkID);
      s.add(userID);
    }
    return owners;
  }
}

function solve(operation_names, argument_lists) {
  const inst = new FileSharing(argument_lists[0][0]);
  const out = [null];
  for (let i = 1; i < operation_names.length; i++) {
    const op = operation_names[i], args = argument_lists[i];
    if (op === "join") out.push(inst.join(args[0]));
    else if (op === "leave") { inst.leave(args[0]); out.push(null); }
    else out.push(inst.request(args[0], args[1]));
  }
  return out;
}

module.exports = solve;
module.exports.solve = solve;
module.exports.FileSharing = FileSharing;
