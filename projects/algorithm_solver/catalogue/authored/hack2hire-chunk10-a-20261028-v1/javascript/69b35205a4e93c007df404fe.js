"use strict";
// Hack2Hire 69b35205a4e93c007df404fe (Design Note-Taking System, variant 1 of 4) over an INFERRED spec; qualification unknown.

class SecondBrainSystem {
  constructor() {
    this.notes = new Map(); // note id -> record
    this.count = 0;
  }

  createNote(title, content, timestamp) {
    this.count += 1;
    const noteId = "note" + this.count;
    this.notes.set(noteId, {n: this.count, title, content, created: timestamp, updated: timestamp});
    return noteId;
  }

  getNote(noteId) {
    const rec = this.notes.get(noteId);
    return rec === undefined ? [] : [rec.title, rec.content, rec.created, rec.updated];
  }

  _replace(rec, title, content, timestamp) {
    rec.title = title; rec.content = content; rec.updated = timestamp;
  }

  updateNote(noteId, title, content, timestamp) {
    const rec = this.notes.get(noteId);
    if (rec === undefined) return false;
    this._replace(rec, title, content, timestamp);
    return true;
  }

  deleteNote(noteId) {
    const rec = this.notes.get(noteId);
    if (rec === undefined) return false;
    this.notes.delete(noteId);
    return true;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "SecondBrainSystem" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new SecondBrainSystem(...argumentLists[0]);
  const allowed = new Set(["createNote", "getNote", "updateNote", "deleteNote"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.SecondBrainSystem = SecondBrainSystem;
