class Solution {
  toGoatLatin(sentence) {
    const words = sentence.split(" ");
    const result = [];
    for (let index = 0; index < words.length; index += 1) {
      let word = words[index];
      if (!"aeiouAEIOU".includes(word[0])) {
        word = word.slice(1) + word[0];
      }
      result.push(word + "ma" + "a".repeat(index + 1));
    }
    return result.join(" ");
  }
}
