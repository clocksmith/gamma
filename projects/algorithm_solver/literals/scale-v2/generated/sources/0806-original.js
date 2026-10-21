function measureTextLines(widthValues, text) {
  let lineCount = 1;
  let lineWidth = 0;
  for (const character of text) {
    const letterIndex = character.charCodeAt(0) - 97;
    const characterWidth = widthValues[letterIndex];
    if (lineWidth + characterWidth <= 100) {
      lineWidth += characterWidth;
    } else {
      lineCount += 1;
      lineWidth = characterWidth;
    }
  }
  return [lineCount, lineWidth];
}
class Solution {
  numberOfLines(widths, s) {
    return measureTextLines(widths, s);
  }
}
