function countLowercase(text) {
  const countsByLetter = new Array(26).fill(0);
  for (const character of text) {
    const letterIndex = character.charCodeAt(0) - 97;
    countsByLetter[letterIndex] += 1;
  }
  return countsByLetter;
}
function countPlateLetters(text) {
  const countsByLetter = new Array(26).fill(0);
  for (const character of text) {
    let letterIndex = character.charCodeAt(0) - 65;
    if (letterIndex >= 0 && letterIndex < 26) {
      countsByLetter[letterIndex] += 1;
    } else {
      letterIndex = character.charCodeAt(0) - 97;
      if (letterIndex >= 0 && letterIndex < 26) {
        countsByLetter[letterIndex] += 1;
      }
    }
  }
  return countsByLetter;
}
function shortestCompletingWord(plateText, words) {
  const requiredCounts = countPlateLetters(plateText);
  let bestWord = null;
  for (const wordText of words) {
    if (bestWord !== null && wordText.length >= bestWord.length) {
      continue;
    }
    const countsByLetter = countLowercase(wordText);
    let completesPlate = true;
    for (let letterIndex = 0; letterIndex < 26; letterIndex += 1) {
      if (countsByLetter[letterIndex] < requiredCounts[letterIndex]) {
        completesPlate = false;
        break;
      }
    }
    if (completesPlate) {
      bestWord = wordText;
    }
  }
  return bestWord;
}
class Solution {
  shortestCompletingWord(licensePlate, words) {
    return shortestCompletingWord(licensePlate, words);
  }
}
