// Original hack2hire:68771a6734c7f781dae2a98b; inferred public-preview contract; qualification unknown.
"use strict";
class PaginationAPI {
  constructor(external) { this.external = external; this.buffer = []; this.offset = 0; this.page = 0; this.calls = 0; this.eof = false; }
  read(count) {
    const result = [];
    while (result.length < count) {
      if (this.offset < this.buffer.length) result.push(this.buffer[this.offset++]);
      else if (this.eof) break;
      else {
        this.buffer = this.external.getPage(this.page++).slice(); this.calls++; this.offset = 0;
        if (!this.buffer.length) this.eof = true;
      }
    }
    return result;
  }
  fetchCount() { return this.calls; }
}
class _ExternalPageFixture {
  constructor(pages) { this.pages = pages.map(page => page.slice()); }
  getPage(page) { return page < this.pages.length ? this.pages[page].slice() : []; }
}

function solve(operationNames, argumentLists) {
  if (!operationNames.length || operationNames.length !== argumentLists.length || operationNames[0] !== "PaginationAPI") throw new Error("exact constructor trace required");
  const instance = new PaginationAPI(new _ExternalPageFixture(argumentLists[0][0])), result = [null], allowed = new Set(["read", "fetchCount"]);
  for (let i = 1; i < operationNames.length; i++) { if (!allowed.has(operationNames[i])) throw new Error("unknown method"); result.push(instance[operationNames[i]](...argumentLists[i]) ?? null); }
  return result;
}
module.exports = solve;
module.exports.PaginationAPI = PaginationAPI;
