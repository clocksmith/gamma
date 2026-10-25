class Solution {
  camelMatch(queries, pattern) {
    function matches(query) {
      let index = 0;
      for (const char of query) {
        if (index < pattern.length && char === pattern[index]) index += 1;
        else if (!("a" <= char && char <= "z")) return false;
      }
      return index === pattern.length;
    }

    const answer = [];
    for (const query of queries) answer.push(matches(query));
    return answer;
  }
}
