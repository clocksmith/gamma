class Solution {
  largeGroupPositions(s) {
    const groups = [];
    let start = 0;
    while (start < s.length) {
      let end = start + 1;
      while (end < s.length && s[end] === s[start]) {
        end += 1;
      }
      if (end - start >= 3) {
        groups.push([start, end - 1]);
      }
      start = end;
    }
    return groups;
  }
}
