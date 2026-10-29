"use strict";
// Hack2Hire 69166e5710632c00111ca0eb (Toy Language Grammar, variant 1 of 2) over an INFERRED spec; qualification unknown.

function fmt(node) {
  if (typeof node === "string") return node;
  return "[" + node.map(fmt).join(", ") + "]";
}

function solve(params, returnType) {
  return "(" + params.map(fmt).join(", ") + ") -> " + fmt(returnType);
}

function formatFunctionType(params, returnType) { return solve(params, returnType); }

module.exports = solve;
module.exports.formatFunctionType = formatFunctionType;
