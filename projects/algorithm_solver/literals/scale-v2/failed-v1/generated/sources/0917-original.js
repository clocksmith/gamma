function reverseLetters(text) {
  const characters = Array.from(text);
  let leftIndex = 0;
  let rightBound = characters.length;
  while (leftIndex + 1 < rightBound) {
    while (leftIndex + 1 < rightBound && !/^\p{L}$/u.test(characters[leftIndex])) {
      leftIndex += 1;
    }
    while (leftIndex + 1 < rightBound && !/^\p{L}$/u.test(characters[rightBound - 1])) {
      rightBound -= 1;
    }
    if (leftIndex + 1 < rightBound) {
      const temporaryCharacter = characters[leftIndex];
      characters[leftIndex] = characters[rightBound - 1];
      characters[rightBound - 1] = temporaryCharacter;
      leftIndex += 1;
      rightBound -= 1;
    }
  }
  return characters.join("");
}
class Solution {
  reverseOnlyLetters(s) {
    return reverseLetters(s);
  }
}
