"use strict";
// Hack2Hire 6a2db7be5117d1b543565e25 (Design Durable Function Call Cache, variant 2 of 2) over an INFERRED spec; qualification unknown.

function encode_(value, out) {
  // type-tagged, self-delimiting serialisation; object keys in sorted order
  if (value === null) out.push("n");
  else if (value === true) out.push("T");
  else if (value === false) out.push("F");
  else if (typeof value === "number") out.push("i" + String(value) + ";");
  else if (typeof value === "string") out.push("s" + value.length + ":" + value);
  else if (Array.isArray(value)) {
    out.push("[");
    for (const item of value) encode_(item, out);
    out.push("]");
  } else {
    out.push("{");
    for (const key of Object.keys(value).sort()) {
      out.push(key.length + ":" + key);
      encode_(value[key], out);
    }
    out.push("}");
  }
}

function createCacheKey(functionName, bound) {
  const out = [functionName.length + ":" + functionName];
  encode_(bound, out);
  return out.join("");
}

class FunctionCallCache {
  constructor(capacity, signatures) {
    this.capacity = capacity;
    this.signatures = new Map(Object.keys(signatures).map((name) => [name, signatures[name].map((p) => p.slice())]));
    this.entries = new Map();  // insertion order is least to most recently used
  }

  call(functionName, args, kwargs) {
    // bind positional, keyword and default arguments in parameter order
    const bound = [];
    this.signatures.get(functionName).forEach((parameter, i) => {
      if (i < args.length) bound.push(args[i]);
      else if (Object.prototype.hasOwnProperty.call(kwargs, parameter[0])) bound.push(kwargs[parameter[0]]);
      else bound.push(parameter[1]);
    });
    const key = createCacheKey(functionName, bound);
    if (this.entries.has(key)) {
      this.entries.delete(key);
      this.entries.set(key, true);
      return true;
    }
    this.entries.set(key, true);
    if (this.entries.size > this.capacity) this.entries.delete(this.entries.keys().next().value);
    return false;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "FunctionCallCache" || argumentLists[0].length !== 2) throw new Error("exact initial constructor required");
  const instance = new FunctionCallCache(...argumentLists[0]);
  const allowed = new Set(["call"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.FunctionCallCache = FunctionCallCache;
