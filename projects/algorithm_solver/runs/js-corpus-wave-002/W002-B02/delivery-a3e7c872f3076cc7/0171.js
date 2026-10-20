function titleToNumber(columnTitle) {
  let value = 0;

  for (const character of columnTitle) {
    value = value * 26 + character.charCodeAt(0) - 64;
  }

  return value;
}
