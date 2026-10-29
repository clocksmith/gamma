"use strict";
// Hack2Hire 69b385d3a4e93c007df405f1 (Design Note-Taking System, variant 4 of 4) over an INFERRED spec; qualification unknown.

class SecondBrainSystem {
  constructor() {
    this.notes = new Map(); // note id -> record
    this.count = 0;
    this.tagIndex = new Map(); // tag -> set of note numbers
  }

  createNote(title, content, timestamp) {
    this.count += 1;
    const noteId = "note" + this.count;
    this.notes.set(noteId, {n: this.count, title, content, created: timestamp, updated: timestamp, low: [title.toLowerCase(), content.toLowerCase()], tags: new Set(), versions: [[title, content]]});
    return noteId;
  }

  getNote(noteId) {
    const rec = this.notes.get(noteId);
    return rec === undefined ? [] : [rec.title, rec.content, rec.created, rec.updated];
  }

  _replace(rec, title, content, timestamp) {
    rec.title = title; rec.content = content; rec.updated = timestamp;
    rec.low = [title.toLowerCase(), content.toLowerCase()];
    rec.versions.push([title, content]);
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
    for (const tag of rec.tags) this.tagIndex.get(tag).delete(rec.n);
    return true;
  }

  searchNotes(keyword) {
    const word = keyword.toLowerCase(), hits = [];
    for (const rec of this.notes.values()) if (rec.low[0].includes(word) || rec.low[1].includes(word)) hits.push(rec);
    hits.sort((a, b) => b.updated - a.updated || a.n - b.n);
    return hits.map((rec) => "note" + rec.n);
  }

  addTag(noteId, tag) {
    const rec = this.notes.get(noteId);
    if (rec === undefined || rec.tags.has(tag)) return false;
    rec.tags.add(tag);
    if (!this.tagIndex.has(tag)) this.tagIndex.set(tag, new Set());
    this.tagIndex.get(tag).add(rec.n);
    return true;
  }

  removeTag(noteId, tag) {
    const rec = this.notes.get(noteId);
    if (rec === undefined || !rec.tags.has(tag)) return false;
    rec.tags.delete(tag);
    this.tagIndex.get(tag).delete(rec.n);
    return true;
  }

  getNotesByTag(tag) {
    const ids = this.tagIndex.get(tag);
    return ids === undefined ? [] : [...ids].sort((a, b) => a - b).map((n) => "note" + n);
  }

  getVersionCount(noteId) {
    const rec = this.notes.get(noteId);
    return rec === undefined ? 0 : rec.versions.length;
  }

  revertNote(noteId, version, timestamp) {
    const rec = this.notes.get(noteId);
    if (rec === undefined || version < 1 || version > rec.versions.length) return false;
    const [title, content] = rec.versions[version - 1];
    this._replace(rec, title, content, timestamp);
    return true;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "SecondBrainSystem" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new SecondBrainSystem(...argumentLists[0]);
  const allowed = new Set(["createNote", "getNote", "updateNote", "deleteNote", "searchNotes", "addTag", "removeTag", "getNotesByTag", "getVersionCount", "revertNote"]);
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
