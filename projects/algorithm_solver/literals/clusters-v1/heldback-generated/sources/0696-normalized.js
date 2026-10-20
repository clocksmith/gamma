function countBinarySubstrings(text) {
  let previousRunLength = 0;
  let currentRunLength = 0;
  let previousCharacter = '';
  let resultCount = 0;
  for (const character of text) {
    if (character === previousCharacter) {
      currentRunLength += 1;
    } else {
      previousRunLength = currentRunLength;
      currentRunLength = 1;
      previousCharacter = character;
    }
    if (currentRunLength <= previousRunLength) {
      resultCount += 1;
    }
  }
  return resultCount;
}
function solve(s) {
  return countBinarySubstrings(s);
}
