function maxProduct(words) {
  const masks = words.map(word => {
    let mask = 0;
    for (const character of word) mask |= 1 << (character.charCodeAt(0) - 97);
    return mask;
  });

  let best = 0;
  for (let left = 0; left < words.length; left++) {
    for (let right = left + 1; right < words.length; right++) {
      if ((masks[left] & masks[right]) === 0) {
        best = Math.max(best, words[left].length * words[right].length);
      }
    }
  }
  return best;
}
