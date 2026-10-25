class Solution {
  countSubstrings(s) {
    let count = 0;
    for (let center = 0; center < s.length; center += 1) {
      for (let offset = 0; offset < 2; offset += 1) {
        let left = center;
        let right = center + offset;
        while (left >= 0 && right < s.length && s[left] === s[right]) {
          count += 1;
          left -= 1;
          right += 1;
        }
      }
    }
    return count;
  }
}
