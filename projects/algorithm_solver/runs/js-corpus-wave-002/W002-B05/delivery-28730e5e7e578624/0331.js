function isValidSerialization(preorder) {
  let slots = 1;
  for (const token of preorder.split(',')) {
    if (slots === 0) return false;
    slots--;
    if (token !== '#') slots += 2;
  }
  return slots === 0;
}
