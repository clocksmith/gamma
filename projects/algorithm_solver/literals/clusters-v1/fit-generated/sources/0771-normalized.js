function encodeTextKey(text) {
  return '$' + text;
}
function countJewelStones(jewelText, stoneText) {
  const jewelKeys = {};
  for (const character of jewelText) {
    const textKey = encodeTextKey(character);
    jewelKeys[textKey] = true;
  }
  let resultCount = 0;
  for (const character of stoneText) {
    const textKey = encodeTextKey(character);
    if (textKey in jewelKeys) {
      resultCount += 1;
    }
  }
  return resultCount;
}
function solve(jewels, stones) {
  return countJewelStones(jewels, stones);
}
