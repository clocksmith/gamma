function encodeTextKey(text) {
  return '$' + text;
}
function compareCharacters(leftText, rightText) {
  return leftText.codePointAt(0) - rightText.codePointAt(0);
}
function specialGroupCount(wordValues) {
  const seenSignatures = {};
  let resultCount = 0;
  for (const word of wordValues) {
    const evenCharacters = [];
    const oddCharacters = [];
    let characterIndex = 0;
    for (const character of word) {
      if (characterIndex % 2 === 0) {
        evenCharacters.push(character);
      } else {
        oddCharacters.push(character);
      }
      characterIndex += 1;
    }
    evenCharacters.sort(compareCharacters);
    oddCharacters.sort(compareCharacters);
    const signature = encodeTextKey(evenCharacters.join('') + oddCharacters.join(''));
    if (seenSignatures[signature] !== true) {
      seenSignatures[signature] = true;
      resultCount += 1;
    }
  }
  return resultCount;
}
class Solution {
  numSpecialEquivGroups(words) {
    return specialGroupCount(words);
  }
}
