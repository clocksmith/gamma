// Original candidate. Contract: https://leetcode.com/problems/number-of-same-end-substrings/
"use strict";

function solve(s, queries) {
  const prefix = Array.from({length: 26}, () => new Int32Array(s.length + 1));
  for (let letter = 0; letter < 26; letter++) {
    for (let i = 0; i < s.length; i++) {
      prefix[letter][i + 1] = prefix[letter][i] +
        (s.charCodeAt(i) - 97 === letter ? 1 : 0);
    }
  }

  return queries.map(([left, right]) => {
    let answer = 0;
    for (const row of prefix) {
      const count = row[right + 1] - row[left];
      // Choose identical endpoints, including a singleton endpoint.
      answer += count * (count + 1) / 2;
    }
    return answer;
  });
}

module.exports = solve;
