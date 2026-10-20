function filterLowercaseVowels(text) {
  let resultText = '';
  for (const character of text) {
    if (!'aeiou'.includes(character)) {
      resultText += character;
    }
  }
  return resultText;
}
function solve(s) {
  return filterLowercaseVowels(s);
}
