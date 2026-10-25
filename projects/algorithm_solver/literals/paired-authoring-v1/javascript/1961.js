class Solution {
  isPrefixString(s, words) {
    let offset = 0;
    for (const word of words) {
      if (!s.startsWith(word, offset)) {
        return false;
      }
      offset += word.length;
      if (offset === s.length) {
        return true;
      }
    }
    return false;
  }
}
