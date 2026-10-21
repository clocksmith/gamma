function isValid(s) {
  const closingCharacters = new Map([['(', ')'], ['[', ']'], ['{', '}']]);
  const expectedClosers = [];
  for (const character of s) {
    if (closingCharacters.has(character)) {
      expectedClosers.push(closingCharacters.get(character));
    } else if (expectedClosers.pop() !== character) {
      return false;
    }
  }
  return expectedClosers.length === 0;
}
