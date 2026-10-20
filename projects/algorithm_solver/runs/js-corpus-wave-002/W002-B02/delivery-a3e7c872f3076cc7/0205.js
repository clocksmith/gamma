function isIsomorphic(s, t) {
  if (s.length !== t.length) {
    return false;
  }

  const forward = new Map();
  const backward = new Map();

  for (let index = 0; index < s.length; index += 1) {
    const left = s[index];
    const right = t[index];

    if (
      (forward.has(left) && forward.get(left) !== right) ||
      (backward.has(right) && backward.get(right) !== left)
    ) {
      return false;
    }

    forward.set(left, right);
    backward.set(right, left);
  }

  return true;
}
