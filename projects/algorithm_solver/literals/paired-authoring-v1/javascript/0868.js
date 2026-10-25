class Solution {
  binaryGap(n) {
    let position = 0;
    let previous = -1;
    let longest = 0;
    while (n > 0) {
      if (n % 2 === 1) {
        if (previous >= 0) {
          longest = Math.max(longest, position - previous);
        }
        previous = position;
      }
      n = Math.floor(n / 2);
      position += 1;
    }
    return longest;
  }
}
