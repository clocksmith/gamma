class Solution {
  spellchecker(wordlist, queries) {
    function vowelKey(lowered) {
      const chars = [];
      for (const char of lowered) chars.push("aeiou".includes(char) ? "*" : char);
      return chars.join("");
    }

    const exact = new Set(wordlist);
    const caseMatches = new Map();
    const vowelMatches = new Map();
    for (const word of wordlist) {
      const lowered = word.toLowerCase();
      const masked = vowelKey(lowered);
      if (!caseMatches.has(lowered)) caseMatches.set(lowered, word);
      if (!vowelMatches.has(masked)) vowelMatches.set(masked, word);
    }
    const answer = [];
    for (const query of queries) {
      if (exact.has(query)) {
        answer.push(query);
        continue;
      }
      const lowered = query.toLowerCase();
      if (caseMatches.has(lowered)) answer.push(caseMatches.get(lowered));
      else answer.push(vowelMatches.get(vowelKey(lowered)) ?? "");
    }
    return answer;
  }
}
