function findTheDifference(s, t) {
  let code = 0;
  for (let index = 0; index < s.length; index++) code ^= s.charCodeAt(index);
  for (let index = 0; index < t.length; index++) code ^= t.charCodeAt(index);
  return String.fromCharCode(code);
}
