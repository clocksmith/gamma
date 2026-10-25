class Solution {
  beforeAndAfterPuzzles(phrases) {
    const firstWords = [];
    const lastWords = [];
    for (const phrase of phrases) {
      const words = phrase.split(" ");
      firstWords.push(words[0]);
      lastWords.push(words[words.length - 1]);
    }
    const answers = new Set();
    for (let left = 0; left < phrases.length; left += 1) {
      for (let right = 0; right < phrases.length; right += 1) {
        if (left !== right && lastWords[left] === firstWords[right]) {
          answers.add(phrases[left] + phrases[right].slice(firstWords[right].length));
        }
      }
    }
    return Array.from(answers).sort();
  }
}
