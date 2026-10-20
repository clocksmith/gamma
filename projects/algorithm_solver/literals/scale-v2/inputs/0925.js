function isLongPressed(nameText, typedText) {
  const nameCharacters = Array.from(nameText);
  const typedCharacters = Array.from(typedText);
  let nameIndex = 0;
  let typedIndex = 0;
  while (nameIndex < nameCharacters.length && typedIndex < typedCharacters.length) {
    if (nameCharacters[nameIndex] !== typedCharacters[typedIndex]) {
      return false;
    }
    let nameBound = nameIndex + 1;
    while (nameBound < nameCharacters.length && nameCharacters[nameBound] === nameCharacters[nameIndex]) {
      nameBound += 1;
    }
    let typedBound = typedIndex + 1;
    while (typedBound < typedCharacters.length && typedCharacters[typedBound] === typedCharacters[typedIndex]) {
      typedBound += 1;
    }
    if (nameBound - nameIndex > typedBound - typedIndex) {
      return false;
    }
    nameIndex = nameBound;
    typedIndex = typedBound;
  }
  return nameIndex === nameCharacters.length && typedIndex === typedCharacters.length;
}
class Solution {
  isLongPressedName(name, typed) {
    return isLongPressed(name, typed);
  }
}
