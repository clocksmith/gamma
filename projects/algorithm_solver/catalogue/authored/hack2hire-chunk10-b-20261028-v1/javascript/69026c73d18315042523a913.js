"use strict";
// Hack2Hire 69026c73d18315042523a913 (Design an Interactive Paginator) over an INFERRED spec; qualification unknown.

class Paginator {
  constructor(totalPages, visibleCount, currentPage) {
    this.total = totalPages; this.visible = visibleCount;
    this.current = Math.min(Math.max(currentPage, 1), totalPages);
  }

  static render(totalPages, visibleCount, currentPage) {
    const shown = Math.min(visibleCount, totalPages);
    const start = Math.max(1, Math.min(currentPage - Math.floor((visibleCount - 1) / 2), totalPages - shown + 1));
    const end = start + shown - 1;
    const parts = [];
    if (currentPage > 1) parts.push("<");
    if (start > 1) parts.push("...");
    for (let page = start; page <= end; page++) parts.push(page === currentPage ? `[${page}]` : String(page));
    if (end < totalPages) parts.push("...");
    if (currentPage < totalPages) parts.push(">");
    return parts.join(" ");
  }

  move(page) {
    this.current = Math.min(Math.max(page, 1), this.total);
    return Paginator.render(this.total, this.visible, this.current);
  }

  next() { return this.move(this.current + 1); }

  prev() { return this.move(this.current - 1); }

  goTo(page) { return this.move(page); }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "Paginator" || argumentLists[0].length !== 3) throw new Error("exact initial constructor required");
  const instance = new Paginator(...argumentLists[0]);
  const allowed = new Set(["next", "prev", "goTo"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.Paginator = Paginator;
