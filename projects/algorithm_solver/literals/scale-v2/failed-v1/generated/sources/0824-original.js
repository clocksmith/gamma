function isWordSeparator(character) {
  const codePoint = character.codePointAt(0);
  return codePoint >= 9 && codePoint <= 13 || codePoint >= 28 && codePoint <= 32 || codePoint === 133 || codePoint === 160 || codePoint === 5760 || codePoint >= 8192 && codePoint <= 8202 || codePoint === 8232 || codePoint === 8233 || codePoint === 8239 || codePoint === 8287 || codePoint === 12288;
}
function splitWhitespaceWords(text) {
  const wordValues = [];
  let wordCharacters = [];
  for (const character of text) {
    if (isWordSeparator(character)) {
      if (wordCharacters.length > 0) {
        wordValues.push(wordCharacters.join(''));
        wordCharacters = [];
      }
    } else {
      wordCharacters.push(character);
    }
  }
  if (wordCharacters.length > 0) {
    wordValues.push(wordCharacters.join(''));
  }
  return wordValues;
}
function convertGoatWords(text) {
  const wordValues = splitWhitespaceWords(text);
  const resultValues = [];
  for (let wordIndex = 0; wordIndex < wordValues.length; wordIndex += 1) {
    let word = wordValues[wordIndex];
    if (!['a', 'e', 'i', 'o', 'u'].includes(word.toLowerCase()[0])) {
      const wordCharacters = Array.from(word);
      word = wordCharacters.slice(1).join('') + wordCharacters[0];
    }
    resultValues.push(word + 'ma' + 'a'.repeat(wordIndex + 1));
  }
  return resultValues.join(' ');
}
class Solution {
  toGoatLatin(sentence) {
    return convertGoatWords(sentence);
  }
}
