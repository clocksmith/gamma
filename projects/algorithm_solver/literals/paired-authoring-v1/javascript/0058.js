class Solution {
  lengthOfLastWord(s) {
    let index = s.length - 1;
    while (index >= 0 && s[index] === " ") {
      index -= 1;
    }
    let length = 0;
    while (index >= 0 && s[index] !== " ") {
      length += 1;
      index -= 1;
    }
    return length;
  }
}
