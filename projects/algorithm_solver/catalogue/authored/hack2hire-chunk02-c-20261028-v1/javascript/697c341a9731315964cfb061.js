"use strict";
// Hack2Hire 697c341a9731315964cfb061 (Accept-Language Header Matching, variant 4) over an INFERRED spec; qualification unknown.
function thousandths(text) {
  const [whole, fraction = ""] = text.split(".");
  return Number(whole) * 1000 + Number((fraction + "000").slice(0, 3));
}
function solve(header, supported) {
  const exact = new Map(), language = new Map();
  let star = null;
  header.split(",").forEach((raw, position) => {
    const trimmed = raw.replace(/^ +| +$/g, ""), cut = trimmed.indexOf(";");
    const token = cut < 0 ? trimmed : trimmed.slice(0, cut);
    const entry = [cut < 0 ? 1000 : thousandths(trimmed.slice(cut + 3)), position];
    if (token === "*") { if (star === null) star = entry; }
    else if (token.length === 2) { if (!language.has(token)) language.set(token, entry); }
    else if (!exact.has(token)) exact.set(token, entry);
  });
  const ranked = [];
  supported.forEach((tag, index) => {
    const found = [exact.get(tag), language.get(tag.slice(0, 2)), star].filter(e => e !== undefined && e !== null);
    if (!found.length || found[0][0] === 0) return;
    ranked.push([-found[0][0], Math.min(...found.map(e => e[1])), index, tag]);
  });
  ranked.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
  return ranked.map(e => e[3]);
}
function parseAcceptLanguage(header, supported) { return solve(header, supported); }
module.exports = solve;
module.exports.parseAcceptLanguage = parseAcceptLanguage;
