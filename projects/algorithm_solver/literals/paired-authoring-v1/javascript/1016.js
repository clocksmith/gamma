class Solution {
  queryString(s, n) {
    const seen = new Set();
    for (let start = 0; start < s.length; start += 1) {
      if (s[start] === "0") continue;
      let value = 0;
      for (let end = start; end < s.length; end += 1) {
        value = value * 2 + (s[end] === "1" ? 1 : 0);
        if (value > n) break;
        seen.add(value);
        if (seen.size === n) return true;
      }
    }
    return seen.size === n;
  }
}
