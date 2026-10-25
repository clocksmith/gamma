class Solution {
  countLetters(text) {
    let previous = null;
    let runLength = 0;
    let total = 0;
    for (const character of text) {
      if (character === previous) {
        runLength += 1;
      } else {
        runLength = 1;
      }
      total += runLength;
      previous = character;
    }
    return total;
  }
}
