"use strict";
// Hack2Hire 69e926affbaf3da641828639 (Convert Snake Case to Camel Case, variant 1) over an INFERRED spec; qualification unknown.
function convert(run) {
  let lead = 0;
  while (lead < run.length && run[lead] === "_") lead++;
  const core = run.slice(lead), words = core.split("_");
  if (words.length < 2 || !words.every(w => /^[a-z0-9]+$/.test(w)) || !(core[0] >= "a" && core[0] <= "z")) return run;
  return run.slice(0, lead) + words[0] + words.slice(1).map(w => w[0].toUpperCase() + w.slice(1)).join("");
}
function solve(src) { return src.replace(/[A-Za-z0-9_]+/g, convert); }
function snakeToCamel(src) { return solve(src); }
module.exports = solve;
module.exports.snakeToCamel = snakeToCamel;
