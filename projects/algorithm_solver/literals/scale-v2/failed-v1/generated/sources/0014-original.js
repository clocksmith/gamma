function longestCommonPrefix(strs) {
  if (strs.length === 0) {
    return '';
  }
  const firstCharacters = Array.from(strs[0]);
  let prefixLength = firstCharacters.length;
  for (let stringIndex = 1; stringIndex < strs.length && prefixLength > 0; stringIndex++) {
    const currentCharacters = Array.from(strs[stringIndex]);
    let characterIndex = 0;
    while (characterIndex < prefixLength && characterIndex < currentCharacters.length && firstCharacters[characterIndex] === currentCharacters[characterIndex]) {
      characterIndex++;
    }
    prefixLength = characterIndex;
  }
  return firstCharacters.slice(0, prefixLength).join('');
}
