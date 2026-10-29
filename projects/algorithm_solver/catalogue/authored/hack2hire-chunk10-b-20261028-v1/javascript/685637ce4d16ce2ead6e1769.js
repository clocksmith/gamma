"use strict";
// Hack2Hire 685637ce4d16ce2ead6e1769 (Encode And Decode) over an INFERRED spec; qualification unknown.

class Codec {
  static flush(pending, runs) {
    for (let k = 0; k < pending.length; k += 8) {
      const chunk = pending.slice(k, k + 8);
      const width = Math.max(...chunk).toString(2).length; // 0 gives "0", width 1
      runs.push("BP[" + [width, ...chunk].join(", ") + "]");
    }
    pending.length = 0;
  }

  encode(nums) {
    const runs = [], pending = [];
    let i = 0;
    const n = nums.length;
    while (i < n) {
      let j = i;
      while (j < n && nums[j] === nums[i]) j++;
      if (j - i >= 3) { Codec.flush(pending, runs); runs.push(`RLE[${nums[i]}, ${j - i}]`); }
      else for (let k = i; k < j; k++) pending.push(nums[k]);
      i = j;
    }
    Codec.flush(pending, runs);
    return runs;
  }

  decode(runs) {
    const out = [];
    for (const run of runs) {
      if (run.startsWith("RLE[")) {
        const [value, count] = run.slice(4, -1).split(", ").map(Number);
        for (let k = 0; k < count; k++) out.push(value);
      } else {
        const fields = run.slice(3, -1).split(", ");
        for (let k = 1; k < fields.length; k++) out.push(Number(fields[k]));
      }
    }
    return out;
  }
}

function solve(operationNames, argumentLists) {
  if (operationNames[0] !== "Codec" || argumentLists[0].length !== 0) throw new Error("exact initial constructor required");
  const instance = new Codec(...argumentLists[0]);
  const allowed = new Set(["encode", "decode"]);
  const result = [null];
  for (let i = 1; i < operationNames.length; i++) {
    if (!allowed.has(operationNames[i])) throw new Error("unknown method");
    const value = instance[operationNames[i]](...argumentLists[i]);
    result.push(value === undefined ? null : value);
  }
  return result;
}

module.exports = solve;
module.exports.Codec = Codec;
