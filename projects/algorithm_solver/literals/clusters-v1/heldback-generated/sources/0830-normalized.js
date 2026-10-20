function findLargeCharacterGroups(text) {
  let characterCount = 0;
  let groupStart = 0;
  let previousCharacter = '';
  const resultValues = [];
  for (const character of text) {
    if (characterCount > 0 && character !== previousCharacter) {
      if (characterCount - groupStart >= 3) {
        resultValues.push([
          groupStart,
          characterCount - 1
        ]);
      }
      groupStart = characterCount;
    }
    previousCharacter = character;
    characterCount += 1;
  }
  if (characterCount - groupStart >= 3) {
    resultValues.push([
      groupStart,
      characterCount - 1
    ]);
  }
  return resultValues;
}
function solve(s) {
  return findLargeCharacterGroups(s);
}
