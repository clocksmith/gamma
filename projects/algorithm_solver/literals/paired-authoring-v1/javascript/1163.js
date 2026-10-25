class Solution {
  lastSubstring(s) {
    let first = 0;
    let second = 1;
    let offset = 0;
    while (second + offset < s.length) {
      if (s[first + offset] === s[second + offset]) {
        offset += 1;
      } else if (s[first + offset] < s[second + offset]) {
        first = Math.max(first + offset + 1, second);
        second = first + 1;
        offset = 0;
      } else {
        second += offset + 1;
        offset = 0;
      }
    }
    return s.slice(first);
  }
}
