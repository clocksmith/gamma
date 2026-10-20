function rearrangeString(s, k) {
  if (k <= 1) return s;
  const remaining = new Int32Array(26);
  const availableAfter = new Int32Array(26);
  for (const character of s) remaining[character.charCodeAt(0) - 97]++;
  const result = [];

  for (let position = 0; position < s.length; position++) {
    let chosen = -1;
    for (let letter = 0; letter < 26; letter++) {
      if (remaining[letter] === 0 || availableAfter[letter] > position) continue;
      if (chosen === -1 || remaining[letter] > remaining[chosen]) chosen = letter;
    }
    if (chosen === -1) return '';
    result.push(String.fromCharCode(97 + chosen));
    remaining[chosen]--;
    availableAfter[chosen] = position + k;
  }
  return result.join('');
}
