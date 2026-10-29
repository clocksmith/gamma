"use strict";
// Hack2Hire 677ae48578175fce2ecdfc0a (Design Inverted Index, variant 1) native class over an INFERRED spec, with a separately declared trace adapter; qualification unknown.
function words(text) { return text.toLowerCase().match(/[a-z0-9]+/g) || []; }
class DocumentLibrary {
  constructor(documents) {
    this.ids = documents.map(d => d[0]);
    this.index = new Map(); // word -> Map(document index -> Set of positions), documents inserted in order
    documents.forEach(([, text], number) => {
      words(text).forEach((word, position) => {
        if (!this.index.has(word)) this.index.set(word, new Map());
        const postings = this.index.get(word);
        if (!postings.has(number)) postings.set(number, new Set());
        postings.get(number).add(position);
      });
    });
  }
  search(phrase) {
    const terms = words(phrase);
    if (!terms.length || terms.some(term => !this.index.has(term))) return [];
    const postings = terms.map(term => this.index.get(term)), result = [];
    for (const [number, starts] of postings[0]) {
      const rest = postings.slice(1).map(p => p.get(number));
      if (rest.some(positions => positions === undefined)) continue;
      for (const start of starts) {
        if (rest.every((positions, offset) => positions.has(start + offset + 1))) { result.push(this.ids[number]); break; }
      }
    }
    return result;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "DocumentLibrary") throw new Error("exact initial constructor required");
  const instance = new DocumentLibrary(...argumentLists[0]);
  const allowed = new Set(["search"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}
module.exports = solve;
module.exports.DocumentLibrary = DocumentLibrary;
