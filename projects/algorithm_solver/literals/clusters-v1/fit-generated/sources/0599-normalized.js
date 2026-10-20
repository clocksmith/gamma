function encodeTextKey(text) {
  return '$' + text;
}
function indexTextPositions(texts) {
  const indicesByText = {};
  for (let textIndex = 0; textIndex < texts.length; textIndex += 1) {
    const textKey = encodeTextKey(texts[textIndex]);
    indicesByText[textKey] = textIndex;
  }
  return indicesByText;
}
function minimumIndexSumTexts(leftTexts, rightTexts) {
  const indicesByText = indexTextPositions(rightTexts);
  let bestIndexSum = leftTexts.length + rightTexts.length;
  let resultTexts = [];
  for (let leftIndex = 0; leftIndex < leftTexts.length; leftIndex += 1) {
    const text = leftTexts[leftIndex];
    const textKey = encodeTextKey(text);
    if (textKey in indicesByText) {
      const rightIndex = indicesByText[textKey];
      const indexSum = leftIndex + rightIndex;
      if (indexSum < bestIndexSum) {
        bestIndexSum = indexSum;
        resultTexts = [text];
      } else if (indexSum === bestIndexSum) {
        resultTexts.push(text);
      }
    }
  }
  return resultTexts;
}
function solve(list1, list2) {
  return minimumIndexSumTexts(list1, list2);
}
