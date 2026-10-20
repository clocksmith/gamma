function removeDuplicateLetters(s) {
  const lastPosition = new Map();
  for (let index = 0; index < s.length; index++) lastPosition.set(s[index], index);

  const included = new Set();
  const stack = [];
  for (let index = 0; index < s.length; index++) {
    const character = s[index];
    if (included.has(character)) continue;

    while (stack.length > 0 &&
      stack[stack.length - 1] > character &&
      lastPosition.get(stack[stack.length - 1]) > index) {
      included.delete(stack.pop());
    }
    stack.push(character);
    included.add(character);
  }
  return stack.join('');
}
