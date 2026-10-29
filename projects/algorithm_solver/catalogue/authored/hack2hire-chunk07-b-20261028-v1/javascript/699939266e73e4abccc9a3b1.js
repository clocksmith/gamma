"use strict";
// Hack2Hire 699939266e73e4abccc9a3b1 (Newspaper Text Alignment) over an INFERRED spec; qualification unknown.

function solve(paragraphs, aligns, width) {
  const border = "*".repeat(width + 2);
  const page = [border];
  for (let p = 0; p < paragraphs.length; p++) {
    const lines = [];
    let current = [], length = 0;
    for (const word of paragraphs[p]) {
      if (current.length && length + 1 + word.length > width) { lines.push(current.join(" ")); current = []; length = 0; }
      length = current.length ? length + 1 + word.length : word.length;
      current.push(word);
    }
    lines.push(current.join(" "));
    for (const line of lines) {
      const pad = " ".repeat(width - line.length);
      page.push("*" + (aligns[p] === "LEFT" ? line + pad : pad + line) + "*");
    }
  }
  page.push(border);
  return page;
}

function formatPage(paragraphs, aligns, width) { return solve(paragraphs, aligns, width); }

module.exports = solve;
module.exports.formatPage = formatPage;
