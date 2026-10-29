"use strict";
// Hack2Hire 6916714410632c00111ca0f3 (Toy Language Grammar, variant 2 of 2) over an INFERRED spec; qualification unknown.

function fmt(node) {
  if (typeof node === "string") return node;
  return "[" + node.map(fmt).join(", ") + "]";
}

function bind(param, arg, binding) {
  if (typeof param === "string") {
    if (param[0] === "T") {
      const text = fmt(arg);
      if (binding.has(param)) return binding.get(param) === text;
      binding.set(param, text);
      return true;
    }
    return param === arg;
  }
  if (!Array.isArray(arg) || arg.length !== param.length) return false;
  for (let k = 0; k < param.length; k++) if (!bind(param[k], arg[k], binding)) return false;
  return true;
}

function render(node, binding) {
  if (typeof node === "string") return binding.has(node) ? binding.get(node) : node;
  return "[" + node.map((child) => render(child, binding)).join(", ") + "]";
}

function solve(params, returnType, args) {
  if (params.length !== args.length) return null;
  const binding = new Map();
  for (let k = 0; k < params.length; k++) if (!bind(params[k], args[k], binding)) return null;
  return render(returnType, binding);
}

function inferReturnType(params, returnType, args) { return solve(params, returnType, args); }

module.exports = solve;
module.exports.inferReturnType = inferReturnType;
