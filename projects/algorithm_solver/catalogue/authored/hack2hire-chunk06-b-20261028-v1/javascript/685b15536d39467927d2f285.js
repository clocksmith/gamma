"use strict";
// Hack2Hire 685b15536d39467927d2f285 (Flatten HTML tags) over an INFERRED spec; qualification unknown.

function solve(root) {
  const tokens = [], nodes = [root], indices = [0];
  while (nodes.length) {
    const node = nodes.pop(), index = indices.pop();
    if (index === 0) tokens.push("<" + node.tag + ">");
    const children = node.children;
    if (index < children.length) {
      nodes.push(node); indices.push(index + 1);
      nodes.push(children[index]); indices.push(0);
    } else tokens.push("</" + node.tag + ">");
  }
  return tokens;
}

function flattenHtml(root) { return solve(root); }

module.exports = solve;
module.exports.flattenHtml = flattenHtml;
