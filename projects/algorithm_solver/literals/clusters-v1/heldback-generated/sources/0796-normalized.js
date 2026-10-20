function buildFailureLengths(patternText) {
  const failureLengths = new Array(patternText.length).fill(0);
  let matchedLength = 0;
  for (let patternIndex = 1; patternIndex < patternText.length; patternIndex += 1) {
    while (matchedLength > 0 && patternText[matchedLength] !== patternText[patternIndex]) {
      matchedLength = failureLengths[matchedLength - 1];
    }
    if (patternText[matchedLength] === patternText[patternIndex]) {
      matchedLength += 1;
    }
    failureLengths[patternIndex] = matchedLength;
  }
  return failureLengths;
}
function isStringRotation(leftText, rightText) {
  if (leftText.length !== rightText.length) {
    return false;
  }
  if (rightText.length === 0) {
    return true;
  }
  const failureLengths = buildFailureLengths(rightText);
  let matchedLength = 0;
  for (let textIndex = 0; textIndex < 2 * leftText.length - 1; textIndex += 1) {
    const character = leftText[textIndex % leftText.length];
    while (matchedLength > 0 && character !== rightText[matchedLength]) {
      matchedLength = failureLengths[matchedLength - 1];
    }
    if (character === rightText[matchedLength]) {
      matchedLength += 1;
    }
    if (matchedLength === rightText.length) {
      return true;
    }
  }
  return false;
}
function solve(s, goal) {
  return isStringRotation(s, goal);
}
