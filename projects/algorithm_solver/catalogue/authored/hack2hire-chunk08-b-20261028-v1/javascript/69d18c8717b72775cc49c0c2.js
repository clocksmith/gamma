"use strict";
// Hack2Hire 69d18c8717b72775cc49c0c2 (Template String Formatter I) over an INFERRED spec; qualification unknown.

function render(text, lookup) {
  const out = [];
  for (let i = 0; i < text.length;) {
    if (text[i] === "{") {
      const j = text.indexOf("}", i);
      out.push(lookup.get(text.slice(i + 1, j)));
      i = j + 1;
    } else {
      let j = text.indexOf("{", i);
      if (j < 0) j = text.length;
      out.push(text.slice(i, j));
      i = j;
    }
  }
  return out.join("");
}

function solve(text, keys, values) {
  const lookup = new Map();
  for (let i = 0; i < keys.length; i++) lookup.set(keys[i], values[i]);
  return render(text, lookup);
}

function formatTemplate(text, keys, values) { return solve(text, keys, values); }

module.exports = solve;
module.exports.formatTemplate = formatTemplate;
