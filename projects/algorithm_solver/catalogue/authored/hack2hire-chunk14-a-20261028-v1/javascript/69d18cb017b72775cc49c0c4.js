"use strict";
// Hack2Hire 69d18cb017b72775cc49c0c4 (Template String Formatter II) over an INFERRED spec; qualification unknown.

const HEAD = ", plural, one{";
const MID = "} other{";

function solve(text, keys, values) {
  const lookup = new Map();
  for (let i = 0; i < keys.length; i++) lookup.set(keys[i], values[i]);
  const out = [];
  let i = 0;
  const length = text.length;
  while (i < length) {
    if (text[i] !== "{") {
      let j = text.indexOf("{", i);
      if (j < 0) j = length;
      out.push(text.slice(i, j));
      i = j;
      continue;
    }
    let j = i + 1;
    while (text[j] !== "}" && text[j] !== ",") j += 1;
    const name = text.slice(i + 1, j);
    if (text[j] === "}") {
      out.push(lookup.has(name) ? lookup.get(name) : text.slice(i, j + 1));
      i = j + 1;
      continue;
    }
    const oneStart = j + HEAD.length;
    const oneEnd = text.indexOf("}", oneStart);
    const otherStart = oneEnd + MID.length;
    const otherEnd = text.indexOf("}", otherStart);
    const end = otherEnd + 2;
    if (lookup.has(name)) {
      const value = lookup.get(name);
      const branch = value === "1" ? text.slice(oneStart, oneEnd) : text.slice(otherStart, otherEnd);
      out.push(branch.split("#").join(value));
    } else {
      out.push(text.slice(i, end));
    }
    i = end;
  }
  return out.join("");
}

function formatTemplate(text, keys, values) { return solve(text, keys, values); }

module.exports = solve;
module.exports.formatTemplate = formatTemplate;
