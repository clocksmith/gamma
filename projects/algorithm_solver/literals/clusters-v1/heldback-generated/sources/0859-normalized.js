function encodeTextKey(text) {
  return '$' + text;
}
function canSwapToMatch(leftText, rightText) {
  const leftCharacters = Array.from(leftText);
  const rightCharacters = Array.from(rightText);
  if (leftCharacters.length !== rightCharacters.length) {
    return false;
  }
  const seenCharacters = {};
  let hasDuplicate = false;
  const mismatchIndices = [];
  for (let characterIndex = 0; characterIndex < leftCharacters.length; characterIndex += 1) {
    const character = leftCharacters[characterIndex];
    const textKey = encodeTextKey(character);
    if (seenCharacters[textKey] === true) {
      hasDuplicate = true;
    }
    seenCharacters[textKey] = true;
    if (character !== rightCharacters[characterIndex]) {
      mismatchIndices.push(characterIndex);
      if (mismatchIndices.length > 2) {
        return false;
      }
    }
  }
  if (mismatchIndices.length === 0) {
    return hasDuplicate;
  }
  if (mismatchIndices.length !== 2) {
    return false;
  }
  const firstIndex = mismatchIndices[0];
  const secondIndex = mismatchIndices[1];
  return leftCharacters[firstIndex] === rightCharacters[secondIndex] && leftCharacters[secondIndex] === rightCharacters[firstIndex];
}
function solve(s, goal) {
  return canSwapToMatch(s, goal);
}
