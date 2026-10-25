class Solution {
  findWordsContaining(words, x) {
    const output = [];
    for (let index = 0; index < words.length; index += 1) {
      for (const character of words[index]) {
        if (character === x) {
          output.push(index);
          break;
        }
      }
    }
    return output;
  }
}
