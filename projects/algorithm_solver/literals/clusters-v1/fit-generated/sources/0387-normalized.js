function countLowercase(text) {
  const countsByLetter = new Array(26).fill(0);
  for (const character of text) {
    const letterIndex = character.charCodeAt(0) - 97;
    countsByLetter[letterIndex] += 1;
  }
  return countsByLetter;
}
function firstUniqueIndex(text) {
  const countsByLetter = countLowercase(text);
  for (let characterIndex = 0; characterIndex < text.length; characterIndex += 1) {
    const letterIndex = text.charCodeAt(characterIndex) - 97;
    if (countsByLetter[letterIndex] === 1) {
      return characterIndex;
    }
  }
  return -1;
}
function solve(s) {
  return firstUniqueIndex(s);
}
