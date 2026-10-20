function reverseAlternatingBlocks(text, blockLength) {
  const characters = text.split('');
  for (let blockStart = 0; blockStart < characters.length; blockStart += 2 * blockLength) {
    let leftIndex = blockStart;
    let rightIndex = blockStart + blockLength;
    if (rightIndex > characters.length) {
      rightIndex = characters.length;
    }
    while (leftIndex + 1 < rightIndex) {
      rightIndex -= 1;
      const savedCharacter = characters[leftIndex];
      characters[leftIndex] = characters[rightIndex];
      characters[rightIndex] = savedCharacter;
      leftIndex += 1;
    }
  }
  return characters.join('');
}
function solve(s, k) {
  return reverseAlternatingBlocks(s, k);
}
