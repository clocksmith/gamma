/* 58. Length of Last Word */
function lengthOfLastWord(s) {
  let index = s.length - 1,
    wordLength = 0;
  while (index >= 0 && s[index] === ' ') {
    index--;
  }
  while (index >= 0 && s[index] !== ' ') {
    wordLength++;
    index--;
  }
  return wordLength;
}
