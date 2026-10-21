function countCharacters(text) {
  const countsByCharacter = {};
  for (const character of text) {
    countsByCharacter[character] = (countsByCharacter[character] || 0) + 1;
  }
  return countsByCharacter;
}
function areAnagrams(leftText, rightText) {
  const leftCounts = countCharacters(leftText);
  const rightCounts = countCharacters(rightText);
  for (const character of leftText) {
    if (leftCounts[character] !== (rightCounts[character] || 0)) {
      return false;
    }
  }
  for (const character of rightText) {
    if (rightCounts[character] !== (leftCounts[character] || 0)) {
      return false;
    }
  }
  return true;
}
class Solution {
  isAnagram(s, t) {
    return areAnagrams(s, t);
  }
}
