function previousVisibleIndex(text, textIndex) {
  let skipCount = 0;
  while (textIndex >= 0) {
    const codeUnit = text.charCodeAt(textIndex);
    if (codeUnit >= 56320 && codeUnit <= 57343 && textIndex > 0) {
      const previousCodeUnit = text.charCodeAt(textIndex - 1);
      if (previousCodeUnit >= 55296 && previousCodeUnit <= 56319) {
        textIndex -= 1;
      }
    }
    const codePoint = text.codePointAt(textIndex);
    if (codePoint === 35) {
      skipCount += 1;
    } else if (skipCount > 0) {
      skipCount -= 1;
    } else {
      return textIndex;
    }
    textIndex -= 1;
  }
  return -1;
}
function equalAfterBackspaces(leftText, rightText) {
  let leftIndex = leftText.length - 1;
  let rightIndex = rightText.length - 1;
  while (leftIndex >= 0 || rightIndex >= 0) {
    leftIndex = previousVisibleIndex(leftText, leftIndex);
    rightIndex = previousVisibleIndex(rightText, rightIndex);
    if (leftIndex < 0 || rightIndex < 0) {
      return leftIndex === rightIndex;
    }
    if (leftText.codePointAt(leftIndex) !== rightText.codePointAt(rightIndex)) {
      return false;
    }
    leftIndex -= 1;
    rightIndex -= 1;
  }
  return true;
}
class Solution {
  backspaceCompare(s, t) {
    return equalAfterBackspaces(s, t);
  }
}
