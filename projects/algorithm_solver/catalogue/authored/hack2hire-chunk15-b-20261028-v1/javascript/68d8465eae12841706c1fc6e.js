"use strict";
// Hack2Hire 68d8465eae12841706c1fc6e (Design File Search Tool) over an INFERRED spec; qualification unknown.

function isWordChar(c) {
  return (c >= "a" && c <= "z") || (c >= "A" && c <= "Z") || (c >= "0" && c <= "9");
}

function lowerAscii(s) {
  let out = "";
  for (const c of s) out += c >= "A" && c <= "Z" ? String.fromCharCode(c.charCodeAt(0) + 32) : c;
  return out;
}

function countInLine(line, target) {
  let count = 0;
  let i = 0;
  const n = line.length;
  while (i < n) {
    if (isWordChar(line[i])) {
      let j = i;
      while (j < n && isWordChar(line[j])) j++;
      if (j - i === target.length && lowerAscii(line.slice(i, j)) === target) count++;
      i = j;
    } else {
      i++;
    }
  }
  return count;
}

function solve(files, word) {
  const target = lowerAscii(word);
  const result = [];
  for (const [name, lines] of files) {
    let total = 0;
    const hits = [];
    for (const line of lines) {
      const c = countInLine(line, target);
      if (c) {
        total += c;
        hits.push(line);
      }
    }
    if (total) result.push([name, String(total), ...hits]);
  }
  return result;
}

function searchFiles(files, word) { return solve(files, word); }

module.exports = solve;
module.exports.searchFiles = searchFiles;
