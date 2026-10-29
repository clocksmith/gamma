"use strict";
// Hack2Hire 69d18cdd17b72775cc49c0c6 (Template String Formatter I) over an INFERRED spec; qualification unknown.

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

function names(text) {
  const out = [];
  for (let i = text.indexOf("{"); i >= 0;) {
    const j = text.indexOf("}", i);
    out.push(text.slice(i + 1, j));
    i = text.indexOf("{", j);
  }
  return out;
}

function solve(text, keys, values) {
  const raw = new Map(), expanded = new Map();
  for (let i = 0; i < keys.length; i++) raw.set(keys[i], values[i]);
  for (const root of names(text)) {
    if (expanded.has(root)) continue;
    const stack = [[root, names(raw.get(root)), 0]];
    while (stack.length) {
      let [key, refs, i] = stack.pop();
      while (i < refs.length && expanded.has(refs[i])) i++;
      if (i < refs.length) {
        stack.push([key, refs, i + 1]);
        stack.push([refs[i], names(raw.get(refs[i])), 0]);
      } else if (!expanded.has(key)) expanded.set(key, render(raw.get(key), expanded));
    }
  }
  return render(text, expanded);
}

function formatTemplate(text, keys, values) { return solve(text, keys, values); }

module.exports = solve;
module.exports.formatTemplate = formatTemplate;
