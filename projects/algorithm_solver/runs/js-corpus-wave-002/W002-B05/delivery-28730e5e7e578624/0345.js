function reverseVowels(s) {
  const characters = s.split('');
  const vowels = new Set('aeiouAEIOU');
  let left = 0;
  let right = characters.length - 1;

  while (left < right) {
    while (left < right && !vowels.has(characters[left])) left++;
    while (left < right && !vowels.has(characters[right])) right--;
    if (left < right) {
      const temporary = characters[left];
      characters[left] = characters[right];
      characters[right] = temporary;
      left++;
      right--;
    }
  }
  return characters.join('');
}
