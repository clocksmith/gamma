function nearestCharacterDistances(text, targetCharacter) {
  const characterValues = Array.from(text);
  const characterCount = characterValues.length;
  const distanceValues = Array(characterCount).fill(characterCount);
  let previousIndex = -characterCount;
  for (let characterIndex = 0; characterIndex < characterCount; characterIndex += 1) {
    if (characterValues[characterIndex] === targetCharacter) {
      previousIndex = characterIndex;
    }
    const distance = characterIndex - previousIndex;
    if (distance < distanceValues[characterIndex]) {
      distanceValues[characterIndex] = distance;
    }
  }
  let nextIndex = 2 * characterCount;
  for (let characterIndex = characterCount - 1; characterIndex >= 0; characterIndex -= 1) {
    if (characterValues[characterIndex] === targetCharacter) {
      nextIndex = characterIndex;
    }
    const distance = nextIndex - characterIndex;
    if (distance < distanceValues[characterIndex]) {
      distanceValues[characterIndex] = distance;
    }
  }
  return distanceValues;
}
function solve(s, c) {
  return nearestCharacterDistances(s, c);
}
