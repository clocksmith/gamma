function lowercaseAscii(text) {
  const uppercaseLetters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const lowercaseLetters = 'abcdefghijklmnopqrstuvwxyz';
  const resultCharacters = [];
  for (const character of text) {
    const letterIndex = uppercaseLetters.indexOf(character);
    if (letterIndex >= 0) {
      resultCharacters.push(lowercaseLetters[letterIndex]);
    } else {
      resultCharacters.push(character);
    }
  }
  return resultCharacters.join('');
}
function solve(s) {
  return lowercaseAscii(s);
}
