function filterLowercaseVowels(text) {
  let resultText = '';
  for (const character of text) {
    if (!'aeiou'.includes(character)) {
      resultText += character;
    }
  }
  return resultText;
}
class Solution {
  removeVowels(s) {
    return filterLowercaseVowels(s);
  }
}
