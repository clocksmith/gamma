"use strict";
// Hack2Hire 69fe591f574d87bc4900686f (Format Articles Within Width) over an INFERRED spec; qualification unknown.

function solve(articles, maxWidth) {
  const lines = [];
  articles.forEach((article, index) => {
    if (index) lines.push("");
    const words = article.split(" ");
    let start = 0, length = words[0].length;
    for (let i = 1; i < words.length; i++) {
      if (length + 1 + words[i].length <= maxWidth) length += 1 + words[i].length;
      else { lines.push(words.slice(start, i).join(" ")); start = i; length = words[i].length; }
    }
    lines.push(words.slice(start).join(" "));
  });
  return lines;
}

function formatArticles(articles, maxWidth) { return solve(articles, maxWidth); }

module.exports = solve;
module.exports.formatArticles = formatArticles;
