function reverseWords(s) {
  const words = s.trim().split(/\s+/);
  if (words.length === 1 && words[0] === '') {
    return '';
  }

  words.reverse();
  return words.join(' ');
}
