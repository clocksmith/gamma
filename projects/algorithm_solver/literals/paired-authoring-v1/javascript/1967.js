function containsText(text, pattern) {
  for (let start = 0; start <= text.length - pattern.length; start += 1) {
    let offset = 0;
    while (offset < pattern.length && text[start + offset] === pattern[offset]) {
      offset += 1;
    }
    if (offset === pattern.length) {
      return true;
    }
  }
  return false;
}


class Solution {
  numOfStrings(patterns, word) {
    let count = 0;
    for (const pattern of patterns) {
      if (containsText(word, pattern)) {
        count += 1;
      }
    }
    return count;
  }
}
