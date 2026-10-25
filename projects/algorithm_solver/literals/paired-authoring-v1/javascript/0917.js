function isLetter(character) {
  return (character >= "A" && character <= "Z") || (character >= "a" && character <= "z");
}

class Solution {
  reverseOnlyLetters(s) {
    const characters = s.split("");
    let left = 0;
    let right = characters.length - 1;
    while (left < right) {
      if (!isLetter(characters[left])) {
        left += 1;
      } else if (!isLetter(characters[right])) {
        right -= 1;
      } else {
        const saved = characters[left];
        characters[left] = characters[right];
        characters[right] = saved;
        left += 1;
        right -= 1;
      }
    }
    return characters.join("");
  }
}
